use crate::tar_metadata::{
    AdamTarMetadataExtract, EntryMetadata, EntryMetadataLocationHash, ExtractTarEntryMetadata,
};
use object_store::{path::Path as ObjPath, ObjectStore};
use std::collections::HashMap;
use std::rc::Rc;
use std::sync::{Arc, Weak};

/// This is effectively a read-only mirror of the filesystem store, with the location of the
/// underlying files. Does not assume that the files within are sorted, but could be made more
/// performant if they are.
///
/// Note: does not support compressed tar files at the moment.
/// Todo: We probably want a generic tar store - for now only adam is supported
struct AdamTarFileObjectStore {
    obj_store_root: String,
    location_to_entry_map: HashMap<String, EntryMetadata>, // gets entry path within the tar
    // archive from object store location path
    weak_self: Weak<AdamTarFileObjectStore>,
}

impl AdamTarFileObjectStore {
    pub fn new_with_locations(
        locations: &Vec<String>,
        tar_path: String,
        prefix: String,
    ) -> Arc<Self> {
        let mut adam_tar_metadata = AdamTarMetadataExtract::new(tar_path, prefix);

        adam_tar_metadata.extract_metadata().unwrap();

        // filter sore to only contain appropriate locations
        for l in locations {
            if adam_tar_metadata.add_entry_if_exists(l.to_string()) {
                println!(
                    "| {} exists: {:?} - added to entry metadata",
                    l,
                    adam_tar_metadata.get_entry(l.to_string())
                )
            } else {
                println!("| {} does not exist - will be ignored", l)
            }
        }

        let adam_tar_metadata = &adam_tar_metadata;

        let location_to_entry_map = adam_tar_metadata
            .entry_location_metadata_map
            .inner()
            .clone();

        Arc::new_cyclic(|s| {
            // Create the actual struct here.
            Self {
                obj_store_root: r"pq+tar://".to_string(),
                location_to_entry_map,
                weak_self: s.clone(),
            }
        })
    }

    fn strong_ref(&self) -> Arc<Self> {
        return self.weak_self.upgrade().unwrap();
    }
}
