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

#[cfg(dead_code)]
struct TarFileObjectStore {
    archive_path: Path,
    /// entries - hashmap
    entries_metadata: HashMap<Location, EntryMetadata>,
}

/// Currently assumes daily files
#[cfg(dead_code)]
fn register_partitioned_tar<T: ParseSingleFile>(single_file_parser: T) {
    T::parse()
}

// NOTE: this can only work for small-ish archives, if we have >100,000 in the archive files for
// example this can use up a lot of memory, and may be better to process in batches.
//
// extract_tar_entry_file_metadata -> Vec<EntryMetadata>
// iter.for_each filename in metadata ->
//
//
//

fn main() {
    let locations =
        AdamTarMetadataExtract::construct_locations_from_date_range("2022-04-01", "2022-04-05");

    println!("{:?}", locations);

    let mut adam_tar_metadata = AdamTarMetadataExtract::new(
        "/home/nvr90/repos/data_engineering/projects/combine_parquet/combpq/blah2020.tar"
            .to_string(),
        "nowboost/tjl/one_minute_data".to_string(),
    );

    println!(
        ">>> indexing metadata for tar file: {}...",
        &adam_tar_metadata.tar_path
    );

    print_adam_metadata_stats(&adam_tar_metadata);

    for l in &locations {
        if adam_tar_metadata.add_entry_if_exists(l.to_string()) {
            println!(
                "{} exists: {:?}",
                l,
                adam_tar_metadata.get_entry(l.to_string())
            )
        } else {
            println!("{} does not exist", l,)
        }
    }
}
