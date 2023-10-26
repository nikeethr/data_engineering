use crate::tar_metadata::{AdamTarMetadataExtract, EntryMetadata, ExtractTarEntryMetadata};

use async_trait::async_trait;
use bytes::Bytes;
use futures::stream::{self, BoxStream};
use object_store::{
    path::Path as ObjPath, GetOptions, GetResult, GetResultPayload, ListResult, MultipartId,
    ObjectMeta, ObjectStore,
};
use std::collections::{BTreeSet, HashMap};
use std::fs::File;
use std::rc::Rc;
use std::sync::{Arc, Weak};
use tokio::io::AsyncWrite;

const TAR_PQ_STORE_BASE_URI: &str = r"tar+pq://";

/// This is effectively a read-only mirror of the filesystem store, with the location of the
/// underlying files. Does not assume that the files within are sorted, but could be made more
/// performant if they are.
///
/// Note: does not support compressed tar files at the moment.
/// Todo: We probably want a generic tar store - for now only adam is supported
#[derive(Debug)]
pub struct AdamTarFileObjectStore {
    obj_store_root: String,
    tar_path: String,
    location_to_entry_map: HashMap<ObjPath, EntryMetadata>, // gets entry path within the tar
    // archive from object store location path
    weak_self: Weak<AdamTarFileObjectStore>,
    // pub for debugging purposes
    pub tar_metadata_all: Vec<EntryMetadata>,
}

impl AdamTarFileObjectStore {
    pub fn new_with_locations(
        locations: Vec<String>,
        tar_path: &String,
        prefix: &String,
    ) -> Arc<Self> {
        let mut adam_tar_metadata =
            AdamTarMetadataExtract::new(tar_path.to_string(), prefix.to_string());

        adam_tar_metadata.extract_metadata().unwrap();

        println!("----------------------------------------------------------------------------------------------------");
        println!("| >>> indexing metadata >>>");
        println!("----------------------------------------------------------------------------------------------------");

        for l in locations {
            if adam_tar_metadata.add_entry_if_exists(l.clone().to_string()) {
                println!(
                    "| {} exists: {:?} - added to entry metadata",
                    l,
                    adam_tar_metadata.get_entry(l.to_string())
                )
            } else {
                println!("| {} does not exist - will be ignored", l)
            }
        }

        // remove mutability
        let adam_tar_metadata = adam_tar_metadata;
        let mut location_to_entry_map = HashMap::new();

        adam_tar_metadata
            .entry_location_metadata_map
            .inner()
            .iter()
            .for_each(|(l, e)| {
                // Using to_owner to get uniquely allocated ownership here to ensure that nothing in
                // adam_tar_metadata is manipulated until this object store is constructed and
                // contains its own unique allocations.

                // create owned data from string
                let l = ObjPath::parse(l).unwrap();
                location_to_entry_map.insert(l, e.to_owned());
            });

        let location_to_entry_map = location_to_entry_map;

        Arc::new_cyclic(|s| {
            // Create the actual struct here.
            Self {
                obj_store_root: TAR_PQ_STORE_BASE_URI.to_string(),
                location_to_entry_map,
                weak_self: s.clone(),
                tar_path: tar_path.clone(),
                tar_metadata_all: adam_tar_metadata.entry_metadata.inner().to_vec(),
            }
        })
    }

    fn strong_ref(&self) -> Arc<Self> {
        return self.weak_self.upgrade().unwrap();
    }
}

impl std::fmt::Display for AdamTarFileObjectStore {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}

// todo: display for AdamTarFileObjectStore
#[async_trait]
impl ObjectStore for AdamTarFileObjectStore {
    async fn get_opts(
        &self,
        location: &ObjPath,
        options: GetOptions,
    ) -> object_store::Result<GetResult> {
        let entry: &EntryMetadata = &self.location_to_entry_map.get(location).unwrap();
        let fp = File::open(&self.tar_path).unwrap();
        let mut pos = entry.raw_file_position as usize;
        let mut size = entry.size as usize;

        let (pos, size) = {
            let pos = &mut pos;
            let size = &mut size;
            match options.range {
                Some(res) => (*pos + res.start, res.end - res.start),
                None => (*pos, *size),
            }
        };

        Ok(GetResult {
            payload: GetResultPayload::File(fp, (&self.tar_path).into()),
            meta: ObjectMeta {
                last_modified: chrono::DateTime::from_timestamp(entry.mtime.try_into().unwrap(), 0)
                    .unwrap(),
                size: entry.size as usize,
                location: location.clone(),
                e_tag: None,
            },
            range: pos..(pos + size),
        })
    }

    async fn head(&self, location: &ObjPath) -> object_store::Result<ObjectMeta> {
        let (location, entry) = self
            .location_to_entry_map
            .iter()
            .find(|(l, _)| l.to_string() == location.to_string())
            .unwrap();

        Ok(ObjectMeta {
            last_modified: chrono::DateTime::from_timestamp(entry.mtime.try_into().unwrap(), 0)
                .unwrap(),
            size: entry.size as usize,
            location: location.clone(),
            e_tag: None,
        })
    }

    async fn list(
        &self,
        prefix: Option<&ObjPath>,
    ) -> object_store::Result<BoxStream<'_, object_store::Result<ObjectMeta>>> {
        let prefix = prefix.cloned().unwrap_or_default();
        Ok(Box::pin(stream::iter(
            self.location_to_entry_map
                .iter()
                .filter_map(move |(location, entry)| {
                    // Don't return for exact prefix match
                    let filter = location
                        .prefix_match(&prefix)
                        .map(|mut x| x.next().is_some())
                        .unwrap_or(false);

                    filter.then(|| {
                        Ok(ObjectMeta {
                            location: location.clone(),
                            last_modified: chrono::DateTime::from_timestamp(
                                entry.mtime.try_into().unwrap(),
                                0,
                            )
                            .unwrap(),
                            size: entry.size as usize,
                            e_tag: None,
                        })
                    })
                }),
        )))
    }

    async fn list_with_delimiter(
        &self,
        prefix: Option<&ObjPath>,
    ) -> object_store::Result<ListResult> {
        let root = ObjPath::default();
        let prefix = prefix.unwrap_or(&root);

        let mut common_prefixes = BTreeSet::new();
        let mut objects = vec![];

        for (k, v) in &self.location_to_entry_map {
            let mut parts = match k.prefix_match(prefix) {
                Some(parts) => parts,
                None => continue,
            };

            // Pop first element
            let common_prefix = match parts.next() {
                Some(p) => p,
                // Should only return children of the prefix
                None => continue,
            };

            if parts.next().is_some() {
                common_prefixes.insert(prefix.child(common_prefix));
            } else {
                let object = ObjectMeta {
                    location: k.clone(),
                    last_modified: chrono::DateTime::from_timestamp(v.mtime.try_into().unwrap(), 0)
                        .unwrap(),
                    size: v.size as usize,
                    e_tag: None,
                };
                objects.push(object);
            }
        }
        Ok(ListResult {
            common_prefixes: common_prefixes.into_iter().collect(),
            objects,
        })
    }

    // ------------------------------------------------------------------
    // The following are not implemented, since this is a read-only store
    // ------------------------------------------------------------------

    async fn put(&self, _location: &ObjPath, _bytes: Bytes) -> object_store::Result<()> {
        unimplemented!()
    }

    async fn put_multipart(
        &self,
        _location: &ObjPath,
    ) -> object_store::Result<(MultipartId, Box<dyn AsyncWrite + Unpin + Send>)> {
        unimplemented!()
    }

    async fn abort_multipart(
        &self,
        _location: &ObjPath,
        _multipart_id: &MultipartId,
    ) -> object_store::Result<()> {
        unimplemented!()
    }

    async fn delete(&self, _location: &ObjPath) -> object_store::Result<()> {
        unimplemented!()
    }

    async fn copy(&self, _from: &ObjPath, _to: &ObjPath) -> object_store::Result<()> {
        unimplemented!()
    }

    async fn copy_if_not_exists(&self, _from: &ObjPath, _to: &ObjPath) -> object_store::Result<()> {
        unimplemented!()
    }
}
