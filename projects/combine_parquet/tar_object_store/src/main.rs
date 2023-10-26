use chrono::prelude::NaiveDate;
use object_store::{path::Path as ObjPath, ObjectStore};
use regex::Regex;
use std::fs::File;
use std::io::Read;
use std::path::Path;
use std::rc::Rc;
use tar::{Archive, Entry};
pub(crate) mod tar_metadata;
pub(crate) mod tar_object_store;
use crate::tar_metadata::{
    print_adam_metadata_stats, AdamTarMetadataExtract, ExtractTarEntryMetadata,
};
use crate::tar_object_store::AdamTarFileObjectStore;
use futures::prelude::*;

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
    let locations =
        AdamTarMetadataExtract::construct_locations_from_date_range("2022-04-01", "2022-04-05");

    let tar_path =
        "/home/nvr90/repos/data_engineering/projects/combine_parquet/combpq/blah2020.tar"
            .to_string();

    let prefix = "nowboost/tjl/one_minute_data".to_string();

    let adam_tar_store = AdamTarFileObjectStore::new_with_locations(locations, &tar_path, &prefix);

    print_adam_metadata_stats(&adam_tar_store.tar_metadata_all);

    let x = adam_tar_store.list(None).await.unwrap();
    println!("{:?}", x.collect::<Vec<_>>().await)
}
