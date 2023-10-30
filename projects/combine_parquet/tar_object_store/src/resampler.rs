use crate::tar_object_store::{self, AdamTarFileObjectStore};

use datafusion::arrow::array::{
    Array, ArrayAccessor, ArrayData, Int64Array, IntervalDayTimeBuilder,
};
use datafusion::arrow::datatypes::{
    DataType, Field, FieldRef, Schema, SchemaBuilder, SchemaRef, UnionFields, UnionMode,
};
use datafusion::arrow::record_batch::{RecordBatchIterator, RecordBatchReader};
use datafusion::arrow::util::pretty;

use std::collections::HashMap;

use chrono::{DateTime, Duration, Utc};
use datafusion::dataframe::DataFrameWriteOptions;
use datafusion::datasource::file_format::FileFormat;
use datafusion::datasource::provider_as_source;
use datafusion::datasource::{
    file_format::{csv::CsvFormat, parquet::ParquetFormat},
    listing::{ListingOptions, ListingTableInsertMode},
};
use datafusion::logical_expr::{ExprSchemable, LogicalPlan, LogicalPlanBuilder};
use datafusion::prelude::*;
use object_store::local::LocalFileSystem;
use std::cmp::{Ordering, PartialOrd};
use std::fmt::Debug;
use std::io::Write;
use std::pin::Pin;
use std::sync::{Arc, Weak};
use tokio::runtime::{Handle, Runtime};
use tokio::sync::mpsc;
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

// TODO: not all frequencies are used
#[allow(dead_code)]
#[derive(Debug, Clone)]
pub enum DataFreq {
    OneMin,
    TenMins,
    OneHour,
    OneDay,
    CustomFreqSeconds(SecondsType),
}

// TODO: probably single file or by station for now
#[allow(dead_code)]
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
#[allow(dead_code)]
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
    output_store: Arc<LocalFileSystem>,
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
                output_store: Arc::new(
                    LocalFileSystem::new_with_prefix(std::path::Path::new("/home/nvr90/tmp/test/"))
                        .unwrap(),
                ),
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
    #[tokio::main(flavor = "multi_thread")]
    pub async fn resample(resampler: Arc<ParquetResampler>) -> tokio::io::Result<()> {
        let start = Utc::now();
        println!("----------------------------------------------------------------------------------------------------");
        println!(">>> Resampling >>>");
        println!("----------------------------------------------------------------------------------------------------");
        println!("| start = {:?}", start.format("%+").to_string());

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

        // construct resampling plan
        println!("| >>> constructiong logical plan...");
        let df = ctx.table(tar_object_store::ADAM_OBS_TABLE_NAME).await?;

        let df = df
            .clone()
            .select_columns(columns.as_slice())?
            .with_column(TIME_RESAMPLED_FIELD, resampler.build_resample_expr())?
            .with_column(
                &station_field,
                ident(&station_field)
                    .cast_to(&DataType::Utf8, df.schema())?
                    .alias(&station_field),
            )?
            .aggregate(
                vec![col(TIME_RESAMPLED_FIELD), ident(&station_field)],
                agg_fields.iter().map(|x| avg(ident(x)).alias(x)).collect(),
            )?
            .sort(vec![
                ident(&station_field).sort(true, false),
                col(TIME_RESAMPLED_FIELD).sort(true, false),
            ])
            .expect("Could not generate logical plan for resampling");

        // --- output ---

        // register object store
        ctx.runtime_env().register_object_store(
            &Url::parse(r"file:///test/").unwrap(),
            resampler.output_store.clone(),
        );

        // register listing table from object store
        let ref_schema = SchemaRef::new(Schema::from(df.schema()).clone());
        // let mut sb = SchemaBuilder::new();
        // ref_schema.fields().iter().for_each(|f| {
        //     let sb = &mut sb;
        //     let f = FieldRef::from(f.clone());
        //     let station_field = station_field.clone();
        //     if station_field.eq(f.name()) {
        //         return;
        //         // sb.push(Field::new(station_field, DataType::Utf8, false));
        //     } else {
        //         sb.push(f.clone());
        //     }
        // });
        // let schema_new = sb.finish();

        ctx.sql(
            "
            create external table 
            test(\"STN_NUM\" VARCHAR, \"AIR_TEMP\" DOUBLE)
            stored as parquet 
            partitioned by (STN_NUM) 
            location '/home/nvr90/tmp/test/'  
            options (create_local_path 'true');
            ",
        )
        .await
        .expect("Uh oh 1");

        let test_table = ctx.table("test").await?;
        println!("{:?}", test_table.schema());

        let xxx = df
            .clone()
            .select(vec![ident("STN_NUM"), ident("AIR_TEMP")])?;

        ctx.register_table("xxx", xxx.into_view())?;

        let xxx = ctx.table("xxx").await?;
        xxx.clone().show_limit(100).await?;

        ctx.sql(
            "
            insert into test (\"STN_NUM\", \"AIR_TEMP\")
            select \"STN_NUM\", \"AIR_TEMP\" from xxx;
            ",
        )
        .await
        .expect("Uh oh 2");
        // sanity check schema
        println!("{:?}", ctx.table("xxx").await?.schema());

        // Xxx.write_table(
        //     "test",
        //     DataFrameWriteOptions::new().with_single_file_output(false),
        // )
        // .await?;

        // println!(">>> BEFORE");
        // println!("{:?}", ref_schema.clone());
        // println!("{:?}", df.schema().fields());
        // println!(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>");

        // ctx.register_listing_table(
        //     "adam_obs_save",
        //     r"file:///test/",
        //     ListingOptions::new(Arc::new(ParquetFormat::default()))
        //         .with_single_file(false)
        //         .with_table_partition_cols(vec![(String::from(r#""STN_NUM""#), DataType::Int64)])
        //         .with_insert_mode(ListingTableInsertMode::AppendNewFiles),
        //     Some(ref_schema.clone()),
        //     None,
        // )
        // .await
        // .expect("Issue with registering issue table schema");

        // // NOTE: theres a bug that causes hive-like write to parititioned object store to fail
        // // cast column to the correct type: https://github.com/apache/arrow-datafusion/pull/7801#issuecomment-1771867480
        // // NOTE: this may have been fixed by now - probably worth looking into updating to higher version.
        // //df.clone().select(vec![ident("STN_NUM").cast_to(&DataType::Int64)?.alias("STN_NUM")].extend())

        // let ref_schema = ref_schema.clone();
        // let df2 = ctx.table("adam_obs_save").await?.select(
        //     ref_schema
        //         .fields()
        //         .iter()
        //         .map(|x| ident(x.name().as_str()).alias(x.name()))
        //         .collect::<Vec<_>>(),
        // )?;
        // let ret = df2.clone().collect().await?;
        // println!("{:?}", ret);

        // df.clone()
        //     .write_table("adam_obs_save", DataFrameWriteOptions::new())
        //     .await
        //     .expect_err("This should fail with schemas not equal");

        // let schema_after = SchemaRef::new(Schema::from(df2.schema()));
        // println!(">>> AFTER");
        // println!("{:?}", schema_after.clone());
        // println!("{:?}", df2.schema().fields());
        // println!(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>");

        // // Now schema is fixed so try again and hopefully it works
        // println!("--- HOPEFULLY SCHEMA HAS FIXED ITSELF ---");

        // df.clone()
        //     .write_table(
        //         "adam_obs_save",
        //         DataFrameWriteOptions::new().with_single_file_output(false),
        //     )
        //     .await?;

        //_df.clone()
        //.select(vec![col("trace_id").cast_to(&DataType::Int64, _df.schema())?.alias("trace_id"), col("partition")])?

        // df.clone()
        //     .write_csv(
        //         format!("/home/nvr90/tmp/blah.csv").as_str(),
        //         DataFrameWriteOptions::new(),
        //         None,
        //     )
        //     .await?;

        // ctx.sql(
        //     r#"
        //         CREATE EXTERNAL TABLE out
        //         STORED AS CSV
        //         PARTITIONED BY ("STN_NUM")
        //         LOCATION '/home/nvr90/tmp/test/'
        //         OPTIONS (
        //             CREATE_LOCAL_PATH 'true',
        //             NULL_VALUE 'NAN'
        //         );

        //         INSERT INTO out SELECT * FROM adam_obs
        //     "#,
        // )
        // .await?;

        // ---
        // create output folder structure: required prior to partitioned output
        // let station_records = df
        //     .clone()
        //     .select(vec![ident(&station_field)])?
        //     .distinct()?
        //     .collect()
        //     .await?;

        // let station_iter = RecordBatchIterator::new(
        //     station_records.clone().into_iter().map(Ok),
        //     station_records.first().unwrap().schema(),
        // );

        // let mut station_out_path = Arc::new(HashMap::<i64, String>::new());

        // let station_iter = station_iter;
        // station_iter.for_each(|r| {
        //     let r = r.unwrap();
        //     let s = r.column(0).as_any().downcast_ref::<Int64Array>().unwrap();
        //     for stn in s {
        //         match stn {
        //             Some(stn) => {
        //                 std::fs::create_dir_all(format!("/home/nvr90/tmp/best/{stn}/")).unwrap();
        //                 // std::fs::File::create(format!("/home/nvr90/tmp/test/{stn}/out.csv")).unwrap();

        //                 let out_path = format!("/home/nvr90/tmp/best/{stn}/out.csv");
        //                 let x = Arc::get_mut(&mut station_out_path)
        //                     .unwrap()
        //                     .insert(stn, out_path);
        //                 let df = df.clone();
        //                 let station_field = station_field.clone();
        //             }
        //             _ => (),
        //         };
        //     }
        // });

        // println!("stations registered");

        // let rt = Arc::new(tokio::runtime::Handle::current());

        // let station_out_path = station_out_path.as_ref();
        // for (stn, out_path) in station_out_path.iter() {
        //     let df = df.clone();
        //     let station_field = station_field.clone();
        //     println!("processing {:?}", stn);
        //     let rt = rt.clone();
        //     tokio::task::block_in_place(move || {
        //         rt.block_on(async move {
        //             df.filter(ident(&station_field).eq(lit(*stn)))
        //                 .unwrap()
        //                 .write_csv(
        //                     out_path.as_str(),
        //                     DataFrameWriteOptions::new().with_single_file_output(true), // use single file output if we're splitting by stations
        //                     None,
        //                 )
        //                 .await
        //                 .unwrap();
        //         });
        //     });
        // }

        // for h in handlers {
        //     h.await?;
        // }
        // ---

        // ctx.sql(
        //     r#"
        //         CREATE EXTERNAL TABLE out
        //         STORED AS CSV
        //         PARTITIONED BY ("STN_NUM")
        //         LOCATION '/home/nvr90/tmp/test/'
        //         OPTIONS (
        //             CREATE_LOCAL_PATH 'true',
        //             NULL_VALUE 'NAN'
        //         );
        //     "#,
        // )
        // .await?;
        // ctx.sql(
        //     r#"
        //         INSERT INTO out SELECT * FROM adam_obs;
        //     "#,
        // )
        // .await?;

        // let ref_schema = SchemaRef::new(Schema::from(df.schema()));

        // println!("{:?}", ref_schema);

        // ctx.runtime_env().register_object_store(
        //     &Url::parse(r"file:///test/").unwrap(),
        //     resampler.output_store.clone(),
        // );

        // println!("| >>> register csv store...");

        // // let (_, station_field_ref) = ref_schema.fields().find(station_field.as_str()).unwrap();

        // // let station_partition_col = (
        // //     station_field_ref.name().to_owned(),
        // //     station_field_ref.data_type().to_owned(),
        // // );

        // // ListingOptions::infer_schema(

        // ctx.register_listing_table(
        //     "adam_obs_save",
        //     r"file:///test/",
        //     ListingOptions::new(Arc::new(CsvFormat::default()))
        //         .with_single_file(false)
        //         .with_table_partition_cols(vec![(&station_field.to_string(), DataType::Int64)]),
        //     Some(ref_schema.clone()),
        //     None,
        // )
        // .await
        // .expect("Issue with registering issue table schema");

        // let df2 = ctx.table("adam_obs_save").await?;

        // let ref_schema_2 = SchemaRef::new(Schema::from(df2.schema()));

        // println!("{:?}", ref_schema_2);

        println!("| >>> write output");

        // Currently distributes by station
        // TODO: fix these to write to actual path, and fix compression
        // TODO: logic to determine whether to partition or not
        // df.clone()
        //     .write_table(
        //         "adam_obs_save",
        //         DataFrameWriteOptions::new()
        //             .with_single_file_output(false)
        //             .with_overwrite(true)
        //             .with_compression(
        //                 datafusion::common::parsers::CompressionTypeVariant::UNCOMPRESSED,
        //             ),
        //     )
        //     .await
        //     .expect("Failed to save to output store");

        // close logging channel
        let end = Utc::now();
        println!("| end = {:?}", end.format("%+").to_string());
        println!("| time_taken = {:?}", end.signed_duration_since(start));
        println!("----------------------------------------------------------------------------------------------------");

        Ok(())
    }
}
