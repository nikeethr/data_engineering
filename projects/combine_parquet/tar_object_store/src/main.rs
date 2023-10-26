use object_store::ObjectStore;

pub(crate) mod tar_metadata;
pub(crate) mod tar_object_store;
use crate::tar_metadata::{print_adam_metadata_stats, AdamTarMetadataExtract};
use crate::tar_object_store::AdamTarFileObjectStore;
use datafusion::arrow::datatypes::DataType;
use datafusion::datasource::{file_format::parquet::ParquetFormat, listing::ListingOptions};
use datafusion::prelude::*;
use futures::prelude::*;
use std::sync::Arc;
use url::Url;

// NOTE: this can only work for small-ish archives, if we have >100,000 in the archive files for
// example this can use up a lot of memory, and may be better to process in batches.
//
// extract_tar_entry_file_metadata -> Vec<EntryMetadata>
// iter.for_each filename in metadata ->
//
//
//

#[tokio::main(flavor = "multi_thread")]
async fn main() {
    // TODO: clean this up into command line args
    let locations =
        AdamTarMetadataExtract::construct_locations_from_date_range("2022-04-01", "2022-04-05");

    let tar_path =
        "/home/nvr90/repos/data_engineering/projects/combine_parquet/combpq/blah2020.tar"
            .to_string();

    let prefix = "nowboost/tjl/one_minute_data".to_string();

    let adam_tar_store = AdamTarFileObjectStore::new_with_locations(locations, &tar_path, &prefix);

    print_adam_metadata_stats(&adam_tar_store.tar_metadata_all);

    let x = adam_tar_store.list(None).await.unwrap();
    println!("{:?}", x.collect::<Vec<_>>().await);

    // TODO: below should be extracted into modules
    let ctx = SessionContext::new();
    ctx.runtime_env().register_object_store(
        &Url::parse(tar_object_store::TAR_PQ_STORE_BASE_URI).unwrap(),
        adam_tar_store,
    );

    ctx.register_listing_table(
        "adam_obs",
        tar_object_store::TAR_PQ_STORE_BASE_URI,
        ListingOptions::new(Arc::new(ParquetFormat::default()))
            .with_file_extension(".parquet")
            .with_table_partition_cols(vec![("date".to_string(), DataType::Date32)])
            .with_file_sort_order(vec![vec![col("date").sort(true, true)]])
            .with_collect_stat(true),
        None,
        None,
    )
    .await
    .unwrap();

    ctx.table("adam_obs")
        .await
        .unwrap()
        .show_limit(10)
        .await
        .unwrap();
}
