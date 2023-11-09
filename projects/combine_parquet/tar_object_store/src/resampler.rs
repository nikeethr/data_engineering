use crate::tar_metadata::AdamTarMetadataExtract;
use crate::tar_object_store::{self, AdamTarFileObjectStore, TAR_PQ_STORE_BASE_URI};

use datafusion::arrow::datatypes::{DataType, Schema, SchemaRef};
use datafusion::arrow::record_batch::RecordBatchReader;

use chrono::Utc;

use datafusion::dataframe::DataFrameWriteOptions;

use clap::ValueEnum;
use datafusion::datasource::{
    file_format::csv::CsvFormat,
    file_format::parquet::ParquetFormat,
    listing::{ListingOptions, ListingTableInsertMode},
};
use datafusion::execution::disk_manager::DiskManagerConfig;
use datafusion::execution::memory_pool::FairSpillPool;
use datafusion::execution::object_store::{DefaultObjectStoreRegistry, ObjectStoreRegistry};
use datafusion::execution::runtime_env::{RuntimeConfig, RuntimeEnv};
use datafusion::logical_expr::ExprSchemable;
use datafusion::prelude::*;
use object_store::local::LocalFileSystem;
use object_store::ObjectStore;

use std::cmp::{Ordering, PartialOrd};
use std::fmt::Debug;
use std::sync::{Arc, Weak};

use url::Url;

// ------------------------------------------------------------------------------------------------
// Data/File frequency helpers
// ------------------------------------------------------------------------------------------------

// TODO: hardcoded reference time to start at 1900-01-01T00:00:00UTC - this should be
// sufficient for the current implementation but may need to revisit if causes issues with how far
// back in time data can be retrieved.
const REFERENCE_DATE: &'static str = "1900-01-01T00:00:00";
const TIME_RESAMPLED_FIELD: &'static str = "time_rsmpl";

// TODO: these constants are named too ADAM specific, they can be more generalized
const STATION_PARTITION_FIELD: &'static str = "stn_partition_id";
const ADAM_RESAMPLED_OBS_TABLE_NAME: &'static str = "adam_obs_resampled";

pub type SecondsType = i64;

pub struct Seconds(SecondsType);

impl PartialEq for Seconds {
    fn eq(&self, other: &Self) -> bool {
        self.0.eq(&other.0)
    }
}

impl PartialOrd for Seconds {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        self.0.partial_cmp(&other.0)
    }
}

/// Allows comparision between two labelled data frequencies.
/// Also implicitly implements [`Into<SecondsType>`]
impl From<DataFreq> for Seconds {
    fn from(s: DataFreq) -> Seconds {
        match s {
            DataFreq::OneMin => Seconds(60),
            DataFreq::TenMins => Seconds(60 * 10),
            DataFreq::OneHour => Seconds(60 * 60),
            DataFreq::OneDay => Seconds(60 * 60 * 24),
            DataFreq::CustomFreqSeconds(inner) => Seconds(inner),
        }
    }
}

// TODO: not all frequencies are used
#[allow(dead_code)]
#[derive(Debug, Clone, ValueEnum)]
pub enum DataFreq {
    OneMin,
    TenMins,
    OneHour,
    OneDay,
    #[value(skip)]
    CustomFreqSeconds(SecondsType),
}

// TODO: probably single file or by station for now
#[allow(dead_code)]
#[derive(Debug, Clone, PartialOrd, PartialEq, ValueEnum)]
pub enum FilePartition {
    ByStation,
    DatafusionDefault,
}

#[allow(dead_code)]
#[derive(Debug, Clone, PartialOrd, PartialEq, ValueEnum)]
pub enum OutputFormat {
    Parquet,
    Csv,
}

// ------------------------------------------------------------------------------------------------
// Resampler
// ------------------------------------------------------------------------------------------------
/// ### Description
///
/// Sets up the necessary input and output data stores as well as query expressions for resampling.
/// Currently only supports downsampling.
///
/// ### Example usage
///
/// ```
/// let adam_tar_store = AdamTarFileObjectStore(...)
/// let pq_resampler = ParquetResampler::new(
///     adam_tar_store,
///     DataFreq::OneMin,
///     DataFreq::OneHour,
///     FileFreq::Monthly,
/// )
/// .with_time_index("LSD")
/// .with_agg_fields(vec!["TEMP", ...])
/// .execute()
/// ```
///
/// ### Restrictions
///
/// * output_data_freq >= input_data_freq, otherwise, error, i.e. only supports down-sample
/// * output_file_partition >= output_data_freq, otherwise, force 1 file
/// * output_type - currently only supports parquet for portablility reasons
/// * input_store - currently only accepts tar files, but could be expanded to general parquet
///   files - though those can probably use datafusion API directly.
/// * currently uses mean() for aggregation
#[allow(dead_code)]
#[derive(Debug)]
pub struct ParquetResampler {
    /// url of input data (current default is a tar object store)
    input_store_url: String,
    /// output directory to store files
    output_path: String,
    /// currently supports parquet or csv - TODO: really should be an enum
    output_format: OutputFormat,
    /// this is the input data frequency (which probably can be inferred), but it's more for sanity
    /// checks against the output_data_freq
    input_data_freq: DataFreq,
    /// this is essentially resampling interval
    output_data_freq: DataFreq,
    /// this the amount of data stored per file, e.g. monthly => month's worth of data in each file
    output_file_partition: FilePartition,
    /// the variables to aggregate for resampling (by default will try to aggregate every variable
    /// which may not work)
    agg_fields: Option<Vec<String>>,
    /// time variable to resample against, defaults to 'time'
    time_index: Option<String>,
    /// station field
    station_field: Option<String>,
    /// station_filter - currently unused
    include_stations: Option<Vec<String>>,
    /// weak pointer to self
    weak_self: Weak<ParquetResampler>,
    /// saved runtime env - same environment will be used for all sessions
    runtime_env: Arc<RuntimeEnv>,
    /// input extension
    input_ext: String,
}

impl ParquetResampler {
    pub fn new(
        input_store: Option<Arc<AdamTarFileObjectStore>>,
        input_path: String,
        output_path: String,
        output_format: OutputFormat,
        input_data_freq: DataFreq,
        output_data_freq: DataFreq,
        output_file_partition: FilePartition,
        time_index: Option<String>,
        station_field: Option<String>,
        agg_fields: Option<Vec<String>>,
        memory_limit_gb: Option<usize>,
    ) -> Arc<Self> {
        // Currently only support downsampling
        assert!(Seconds::from(input_data_freq.clone()) <= Seconds::from(output_data_freq.clone()));

        let runtime_env = match &input_store {
            Some(tar_store) => Self::create_rt_env(
                tar_store.clone(),
                memory_limit_gb,
                &TAR_PQ_STORE_BASE_URI.to_string(),
            ),
            None => Self::create_rt_env(
                Arc::new(LocalFileSystem::default()),
                memory_limit_gb,
                &input_path,
            ),
        };

        let input_url = if let Some(_) = input_store {
            TAR_PQ_STORE_BASE_URI.to_string()
        } else {
            input_path
        };

        let input_ext = if let Some(_) = input_store {
            tar_object_store::PQ_EXTENSION.to_string()
        } else {
            String::default()
        };

        Arc::new_cyclic(|s| {
            // Create the actual struct here.
            Self {
                input_store_url: input_url,
                output_path,
                output_format,
                input_data_freq,
                output_data_freq,
                output_file_partition,
                agg_fields,
                time_index,
                station_field,
                include_stations: None,
                weak_self: s.clone(),
                runtime_env,
                input_ext,
            }
        })
    }

    fn create_rt_env(
        input_store: Arc<dyn ObjectStore>,
        memory_limit_gb: Option<usize>,
        url: &String,
    ) -> Arc<RuntimeEnv> {
        // Os chooses specified paths
        println!(
            "| >>> Registering runtime config, memory_limit_gb={:?}",
            memory_limit_gb
        );
        let rt = RuntimeConfig::new().with_disk_manager(DiskManagerConfig::new());

        // setup memory limits
        let gb_to_b = |x| (x * 1024 * 1024 * 1024) as usize;
        let rt = match memory_limit_gb {
            None => rt,
            Some(mem_gb) => rt.with_memory_pool(Arc::new(FairSpillPool::new(gb_to_b(mem_gb)))),
        };

        // insert object stores
        let rt = rt.with_object_store_registry({
            // this includes the local filesstem by default so we only need to
            // register the tar store
            let obj_store_registry = DefaultObjectStoreRegistry::new();
            obj_store_registry.register_store(&Url::parse(url.as_str()).unwrap(), input_store);
            Arc::new(obj_store_registry)
        });

        Arc::new(RuntimeEnv::new(rt).expect("Could not create runtime environment"))
    }

    // TODO: currently there's no usecase for strong ref, but generally it can be used to upgrade a
    // weak ref in the event that the Arc gets dropped, while the allocation still exists.
    #[allow(dead_code)]
    pub fn strong_ref(&self) -> Arc<Self> {
        return self.weak_self.upgrade().unwrap();
    }

    fn build_resample_expr(&self) -> Expr {
        let time_interval_str = match self.output_data_freq.clone() {
            DataFreq::OneMin => "1 minute",
            DataFreq::TenMins => "10 minutes",
            DataFreq::OneHour => "1 hour",
            DataFreq::OneDay => "1 day",
            // TODO: Currently does not handle arbitrary data intervals
            DataFreq::CustomFreqSeconds(_) => unimplemented!(),
        };

        let time_index = match self.time_index.clone() {
            Some(t) => t,
            None => "time".to_string(),
        };

        call_fn(
            "date_bin",
            vec![
                lit(time_interval_str),
                ident(time_index),
                lit(REFERENCE_DATE),
            ],
        )
        .unwrap()
    }

    fn session_ctx_with_runtime_config(&self) -> SessionContext {
        SessionContext::new_with_config_rt(SessionConfig::new(), self.runtime_env.clone())
    }

    /// Blocks current thread and sets up the main resampling task
    ///
    /// Only this part needs to be async as it performs the loading, querying and saving, all the
    /// setup can be done as single sync thread prior to running the resampling.
    ///
    /// CAUTION: Avoid spawning blocking threads here as it will slow down any data fusion
    /// functionality. Any thread spawning required to custom batch certain operations
    /// (e.g. splitting queries by month) should be done outside of this function system threads
    /// and/or use a separate tokio runtime with configured blocking limits, to avoid spawning too
    /// many blocking IO threads that interfere with datafusion. Datafusion gets really confused
    /// with nested green threads, unless done properly.
    ///
    /// TODO: split out this function
    pub fn resample_async_wrapper(
        resampler: Arc<ParquetResampler>,
        thread_count: Option<usize>,
        provided_schema: Option<SchemaRef>,
    ) {
        let tokio_runtime = match thread_count {
            None => tokio::runtime::Builder::new_multi_thread().build().unwrap(),
            Some(n) => tokio::runtime::Builder::new_multi_thread()
                .worker_threads(n)
                .build()
                .unwrap(),
        };

        println!("| >>> Input schema: {:?}", provided_schema);
        // block current thread and run main resampling task
        tokio_runtime.block_on(async move {
            resampler
                .resample(provided_schema)
                .await
                .expect("Resampling was unsuccessful - see stack trace or logs for more info")
        })
    }

    async fn resample(&self, provided_schema: Option<SchemaRef>) -> tokio::io::Result<()> {
        let start = Utc::now();
        println!("+---------------------------------------------------------------------------------------------------");
        println!("| >>> Resampling >>>");
        println!("+---------------------------------------------------------------------------------------------------");
        println!("| start = {:?}", start.format("%+").to_string());

        // ---
        // TODO: system based runtime config: datafusion can get memory hungry, so it may
        // be wise to configure diskmanager/cachemanager/memorylimits appropriately.
        // ---
        let ctx = self.session_ctx_with_runtime_config();

        // ---
        // TODO: split out these stages into individual functions
        // ---

        println!("| >>> register input table parquet table from tar store...");

        ctx.register_listing_table(
            tar_object_store::ADAM_OBS_TABLE_NAME,
            &self.input_store_url,
            ListingOptions::new(Arc::new(
                ParquetFormat::default().with_enable_pruning(Some(true)),
            ))
            .with_file_extension(&self.input_ext)
            .with_table_partition_cols(vec![("date".to_string(), DataType::Date32)])
            .with_file_sort_order(vec![vec![col("date").sort(true, true)]])
            .with_insert_mode(ListingTableInsertMode::Error),
            provided_schema,
            None,
        )
        .await
        .expect("Could not register input parquet tar table");

        // --- resample ---
        // clone Vec<String> into a &[&str] because that's what the query expects instead of
        // Vec<String>. I'm too lazy to look up how to do this using ::from, and too even more lazy
        // to write my own trait so this ugly mess is what you get.

        let station_field = self.station_field.clone().unwrap();
        let time_index = self.time_index.clone().unwrap();
        let agg_fields = self.agg_fields.clone().unwrap();
        let columns = {
            // temporary mutabiilty
            let mut columns = vec![&station_field, &time_index];
            columns.extend(&agg_fields);
            columns.iter().map(|x| x.as_str()).collect::<Vec<&str>>()
        };

        // --- construct resampling plan ---
        println!("| >>> constructiong logical plan...");
        let df = ctx.table(tar_object_store::ADAM_OBS_TABLE_NAME).await?;

        // note: constructing lowercase alias for most fields in order to normalize
        let df = df
            .clone()
            .select_columns(columns.as_slice())?
            .with_column(TIME_RESAMPLED_FIELD, self.build_resample_expr())?
            .aggregate(
                vec![
                    col(TIME_RESAMPLED_FIELD),
                    ident(&station_field)
                        .alias(station_field.to_lowercase())
                        .cast_to(&DataType::Utf8, df.schema())?,
                ],
                agg_fields
                    .iter()
                    .map(|x| avg(ident(x)).alias(x.to_lowercase()))
                    .collect(),
            )?
            .sort(vec![col(TIME_RESAMPLED_FIELD).sort(true, false)])
            .expect("Could not generate logical plan for resampling");

        // --- register local listing table ---
        let ref_schema = SchemaRef::new(Schema::from(df.schema()).clone());
        // -----
        // Equivilent to:
        // ctx.sql(
        //     r#"
        //     create external table
        //     test("stn_id" VARCHAR, "air_temp" DOUBLE, "stn_num" VARCHAR, ...)
        //     stored as csv
        //     with header row
        //     partitioned by (stn_num)
        //     location <output_path>
        //     options (
        //         create_local_path 'true',
        //         insert_mode 'append_new_files',
        //     );
        //     "#,
        // )
        // -----

        std::fs::create_dir_all(&self.output_path)
            .expect("Err: could not create output directory path");

        let listing_opts = ListingOptions::new(match self.output_format {
            // TODO: probably should be an enum
            OutputFormat::Parquet => Arc::new(ParquetFormat::default()),
            OutputFormat::Csv => Arc::new(CsvFormat::default().with_has_header(true)),
        })
        .with_insert_mode(ListingTableInsertMode::AppendNewFiles);

        let listing_opts = match self.output_file_partition {
            FilePartition::ByStation => {
                // dummy field stn_id_partition - used for partitioning.
                // TODO: this assumes that the data does not have this field already a
                // sanity check needs to be performed.
                listing_opts.with_table_partition_cols(vec![(
                    STATION_PARTITION_FIELD.to_string(),
                    DataType::Utf8,
                )])
            }
            FilePartition::DatafusionDefault => listing_opts,
        };

        ctx.register_listing_table(
            ADAM_RESAMPLED_OBS_TABLE_NAME,
            &self.output_path,
            listing_opts,
            Some(ref_schema.clone()),
            None,
        )
        .await
        .expect("Could not register external output table");

        // --- write output ---
        println!(
            "| >>> write output ({:?}): {:?}",
            self.output_format, self.output_path
        );

        // adjust column cast so it works properly... partition column has to be a string or it
        // doesn't seem to work. Also partition field will be eaten up, so needs to be duplicated.

        let df = match self.output_file_partition {
            FilePartition::ByStation => df.clone().with_column(
                STATION_PARTITION_FIELD,
                ident(station_field.to_lowercase()).cast_to(&DataType::Utf8, df.schema())?,
            )?,
            FilePartition::DatafusionDefault => df.clone(),
        };

        df.clone()
            .write_table(
                ADAM_RESAMPLED_OBS_TABLE_NAME,
                DataFrameWriteOptions::new().with_single_file_output(false),
            )
            .await
            .expect("Failed to write to output");

        let end = Utc::now();
        println!("| end = {:?}", end.format("%+").to_string());
        println!("| time_taken = {:?}", end.signed_duration_since(start));
        println!("+---------------------------------------------------------------------------------------------------");

        Ok(())
    }
}
