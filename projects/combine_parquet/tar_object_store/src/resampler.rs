use crate::tar_object_store::{self, AdamTarFileObjectStore};

use datafusion::arrow::datatypes::{DataType, Field, Schema, SchemaRef};
use datafusion::arrow::record_batch::RecordBatchReader;

use chrono::Utc;
use datafusion::dataframe::DataFrameWriteOptions;

use clap::ValueEnum;
use datafusion::datasource::{
    file_format::csv::CsvFormat,
    file_format::parquet::ParquetFormat,
    listing::{ListingOptions, ListingTableInsertMode},
};
use datafusion::execution::disk_manager::{DiskManager, DiskManagerConfig};
use datafusion::logical_expr::ExprSchemable;
use datafusion::prelude::*;
use object_store::local::LocalFileSystem;
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
    /// input metadata of tar achive as an object store
    input_store: Arc<AdamTarFileObjectStore>,
    /// output directory to store files
    output_path: String,
    /// currently supports parquet or csv - TODO: really should be an enum
    output_format: String,
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
    /// for saving output
    output_store: Arc<LocalFileSystem>,
}

impl ParquetResampler {
    pub fn new(
        input_store: Arc<AdamTarFileObjectStore>,
        output_path: String,
        output_format: String,
        input_data_freq: DataFreq,
        output_data_freq: DataFreq,
        output_file_partition: FilePartition,
        time_index: Option<String>,
        station_field: Option<String>,
        agg_fields: Option<Vec<String>>,
    ) -> Arc<Self> {
        // Currently only support downsampling
        assert!(Seconds::from(input_data_freq.clone()) <= Seconds::from(output_data_freq.clone()));

        Arc::new_cyclic(|s| {
            // Create the actual struct here.
            Self {
                input_store,
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
                // TODO: change this currently for testing
                output_store: Arc::new(LocalFileSystem::new()),
            }
        })
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

    // only this part needs to be async as it performs the loading, querying and saving, all the
    // setup can be done as single sync thread.
    /// TODO: split out this function
    #[tokio::main(flavor = "multi_thread")]
    pub async fn resample(resampler: Arc<ParquetResampler>) -> tokio::io::Result<()> {
        let start = Utc::now();
        println!("----------------------------------------------------------------------------------------------------");
        println!(">>> Resampling >>>");
        println!("----------------------------------------------------------------------------------------------------");
        println!("| start = {:?}", start.format("%+").to_string());

        // ---
        // TODO: system based runtime config: datafusion can get memory hungry, so it may
        // be wise to configure diskmanager/cachemanager/memorylimits appropriately.
        // ---
        let ctx = SessionContext::new();

        // ---
        // TODO: split out these stages into individual functions
        // ---

        // --- register input ---
        // register input object store - tar file
        ctx.runtime_env().register_object_store(
            &Url::parse(tar_object_store::TAR_PQ_STORE_BASE_URI).unwrap(),
            resampler.input_store.clone(),
        );

        println!("| >>> register input table parquet table from tar store...");

        ctx.register_listing_table(
            tar_object_store::ADAM_OBS_TABLE_NAME,
            tar_object_store::TAR_PQ_STORE_BASE_URI,
            ListingOptions::new(Arc::new(ParquetFormat::default()))
                .with_file_extension(tar_object_store::PQ_EXTENSION)
                .with_table_partition_cols(vec![("date".to_string(), DataType::Date32)])
                .with_file_sort_order(vec![vec![col("date").sort(true, true)]])
                .with_insert_mode(ListingTableInsertMode::Error),
            None,
            None,
        )
        .await
        .expect("Could not register input parquet tar table");

        // --- resample ---
        // clone Vec<String> into a &[&str] because that's what the query expects instead of
        // Vec<String>. I'm too lazy to look up how to do this using ::from, and too even more lazy
        // to write my own trait so this ugly mess is what you get.

        let station_field = resampler.station_field.clone().unwrap();
        let time_index = resampler.time_index.clone().unwrap();
        let agg_fields = resampler.agg_fields.clone().unwrap();
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
            .with_column(TIME_RESAMPLED_FIELD, resampler.build_resample_expr())?
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
            .sort(vec![
                ident(station_field.to_lowercase()).sort(true, false),
                col(TIME_RESAMPLED_FIELD).sort(true, false),
            ])
            .expect("Could not generate logical plan for resampling");

        // --- register local object store & listing table ---

        // TODO: This can eventually be extended to any implemented object store protocol
        // e.g. cloud/hive/nfs/in-memory/ftp/http etc.
        ctx.runtime_env().register_object_store(
            &Url::parse(r"file://local").unwrap(),
            resampler.output_store.clone(),
        );

        let ref_schema = SchemaRef::new(Schema::from(df.schema()).clone());

        // ref_schema.clone().fields().iter().chain(Some(Field::new()).iter())

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
        let listing_opts = ListingOptions::new(match resampler.output_format.as_str() {
            // TODO: probably should be an enum
            "parquet" => Arc::new(ParquetFormat::default()),
            "csv" => Arc::new(CsvFormat::default().with_has_header(true)),
            &_ => todo!(),
        })
        .with_insert_mode(ListingTableInsertMode::AppendNewFiles);

        let listing_opts = match resampler.output_file_partition {
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

        std::fs::create_dir_all(&resampler.output_path)
            .expect("Err: could not create output directory path");

        ctx.register_listing_table(
            ADAM_RESAMPLED_OBS_TABLE_NAME,
            &resampler.output_path,
            listing_opts,
            Some(ref_schema.clone()),
            None,
        )
        .await
        .expect("Could not register external output table");

        // --- write output ---
        println!("| >>> write output");

        // adjust column cast so it works properly... partition column has to be a string or it
        // doesn't seem to work. Also partition field will be eaten up, so needs to be duplicated.
        df.clone()
            // .select_columns(
            //     ref_schema
            //         .clone()
            //         .fields()
            //         .iter()
            //         .map(|x| x.name().as_str())
            //         .collect::<Vec<_>>()
            //         .as_slice(),
            // )?
            .with_column(
                STATION_PARTITION_FIELD,
                ident(station_field.to_lowercase()).cast_to(&DataType::Utf8, df.schema())?,
            )?
            .write_table(
                ADAM_RESAMPLED_OBS_TABLE_NAME,
                DataFrameWriteOptions::new().with_single_file_output(false),
            )
            .await
            .expect("Failed to write to output");

        let end = Utc::now();
        println!("| end = {:?}", end.format("%+").to_string());
        println!("| time_taken = {:?}", end.signed_duration_since(start));
        println!("----------------------------------------------------------------------------------------------------");

        Ok(())
    }
}
