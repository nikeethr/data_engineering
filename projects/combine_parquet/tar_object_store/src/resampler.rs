
use crate::tar_object_store::{self, AdamTarFileObjectStore};

use datafusion::arrow::datatypes::{DataType};

use datafusion::dataframe::DataFrameWriteOptions;
use datafusion::datasource::{
    file_format::{parquet::ParquetFormat},
    listing::{ListingOptions, ListingTableInsertMode},
};
use datafusion::prelude::*;
use object_store::{local::LocalFileSystem, ObjectStore};
use std::cmp::{Ordering, PartialOrd};
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

#[derive(Debug, Clone)]
pub enum DataFreq {
    OneMin,
    TenMins,
    OneHour,
    OneDay,
    CustomFreqSeconds(SecondsType),
}

/// TODO: probably single file or by station for now
#[derive(Debug, Clone, PartialOrd, PartialEq)]
pub enum FilePartition {
    SingleFile,
    ByStation,
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
#[derive(Debug)]
pub struct ParquetResampler {
    input_store: Arc<AdamTarFileObjectStore>,
    // this is the input data frequency (which probably can be inferred), but it's more for sanity
    // checks against the output_data_freq
    input_data_freq: DataFreq,
    // this is essentially resampling interval
    output_data_freq: DataFreq,
    // this the amount of data stored per file, e.g. monthly => month's worth of data in each file
    output_file_partition: FilePartition,
    // the variables to aggregate for resampling (by default will try to aggregate every variable
    // which may not work)
    agg_fields: Option<Vec<String>>,
    // time variable to resample against, defaults to 'time'
    time_index: Option<String>,
    // station field
    station_field: Option<String>,
    // station_filter
    include_stations: Option<Vec<String>>,
    // weak pointer to self
    weak_self: Weak<ParquetResampler>,
    // for saving output
    dest: Arc<LocalFileSystem>,
}

impl ParquetResampler {
    pub fn new(
        input_store: Arc<AdamTarFileObjectStore>,
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
                input_data_freq,
                output_data_freq,
                output_file_partition,
                agg_fields,
                time_index,
                station_field,
                include_stations: None,
                weak_self: s.clone(),
                // TODO: change this currently for testing
                dest: Arc::new(
                    LocalFileSystem::new_with_prefix(std::path::Path::new("/home/nvr90/tmp/test/"))
                        .unwrap(),
                ),
            }
        })
    }

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
    #[tokio::main(flavor = "multi_thread")]
    pub async fn resample(resampler: Arc<ParquetResampler>) -> tokio::io::Result<()> {
        let ctx = SessionContext::new();

        ctx.runtime_env().register_object_store(
            &Url::parse(tar_object_store::TAR_PQ_STORE_BASE_URI).unwrap(),
            resampler.input_store.clone(),
        );

        // register input object store - tar file
        ctx.register_listing_table(
            tar_object_store::ADAM_OBS_TABLE_NAME,
            tar_object_store::TAR_PQ_STORE_BASE_URI,
            ListingOptions::new(Arc::new(ParquetFormat::default()))
                .with_file_extension(".parquet")
                .with_table_partition_cols(vec![("date".to_string(), DataType::Date32)])
                .with_file_sort_order(vec![vec![col("date").sort(true, true)]])
                .with_insert_mode(ListingTableInsertMode::Error),
            None,
            None,
        )
        .await?;

        // clone Vec<String> into a &[&str] because that's what the query expects instead of
        // Vec<String>. I'm too lazy to look up how to do this using ::from, and too even more lazy
        // to write my own trait so this ugly mess is what you get.
        let agg_fields = resampler.agg_fields.clone().unwrap();
        let station_field = resampler.station_field.clone().unwrap();
        let time_index = resampler.time_index.clone().unwrap();
        let mut columns = Vec::<String>::new();
        columns.push(station_field.clone());
        columns.push(time_index.clone());
        columns.append(&mut agg_fields.clone());
        let columns = &columns.iter().map(|x| x.as_str()).collect::<Vec<_>>();

        // remove mutability
        let station_field = station_field;
        let agg_fields = agg_fields;

        // construct resampling plan
        let df = ctx.table(tar_object_store::ADAM_OBS_TABLE_NAME).await?;
        let df = df
            .clone()
            .select_columns(columns.as_slice())?
            .with_column(TIME_RESAMPLED_FIELD, resampler.build_resample_expr())?
            .aggregate(
                vec![col(TIME_RESAMPLED_FIELD), ident(&station_field)],
                agg_fields.iter().map(|x| avg(ident(x))).collect(),
            )?
            .sort(vec![
                ident(&station_field).sort(true, false),
                col(TIME_RESAMPLED_FIELD).sort(true, false),
            ])?;

        ctx.register_csv(
            "adam_obs_save",
            "/home/nvr90/tmp/test",
            CsvReadOptions::new().table_partition_cols(vec![(station_field, DataType::Utf8)]),
        );
        // register output format
        // ctx.register_listing_table(
        //     "adam_obs_save",
        //     r"file:///home/nvr90/tmp/test/",
        //     ListingOptions::new(Arc::new(CsvFormat::default()))
        //         .with_table_partition_cols(vec![(station_field, DataType::Utf8)])
        //         .with_file_sort_order(vec![vec![col(TIME_RESAMPLED_FIELD).sort(true, true)]]),
        //     Some(SchemaRef::new(Schema::from(df.schema().clone()))),
        //     None,
        // )
        // .await?;

        // Currently distributes by station
        // TODO: fix these to write to actual path, and fix compression
        // TODO: logic to determine whether to partition or not
        df.clone()
            .write_table(
                "adam_obs_save",
                DataFrameWriteOptions::new()
                    .with_single_file_output(false)
                    .with_compression(
                        datafusion::common::parsers::CompressionTypeVariant::UNCOMPRESSED,
                    ),
            )
            .await?;

        Ok(())
    }
}
