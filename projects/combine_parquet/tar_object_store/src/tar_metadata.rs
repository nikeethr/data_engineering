use chrono::prelude::NaiveDate;

use datafusion::parquet::data_type::AsBytes;
use regex::Regex;
use rkyv::{Archive, Deserialize, Serialize};

use std::fs::File;

use std::rc::Rc;

// TODO: update this to command line arg
pub const DEFAULT_CACHE_PATH: &'static str = "/tmp/tarpq_cache/.tarpq_s";

#[derive(Debug, Clone)]
pub struct EntryMetadataLocationHash {
    inner: Rc<std::collections::HashMap<String, EntryMetadata>>,
}

impl EntryMetadataLocationHash {
    pub fn new() -> Self {
        EntryMetadataLocationHash {
            inner: Rc::new(std::collections::HashMap::<String, EntryMetadata>::new()),
        }
    }

    fn insert(&mut self, l: String, e: EntryMetadata) {
        let inner_mut = Rc::get_mut(&mut self.inner).unwrap(); // get mutable reference counter
        inner_mut.insert(l, e);
    }

    pub fn inner(&self) -> &std::collections::HashMap<String, EntryMetadata> {
        &self.inner
    }
}

#[derive(Debug, Clone)]
pub struct EntryMetadataVec {
    inner: Rc<Vec<EntryMetadata>>,
    pub cached: bool,
    pub cache_path: Option<String>,
}

impl EntryMetadataVec {
    pub fn new() -> Self {
        let default = EntryMetadataVec {
            inner: Rc::new(Vec::<EntryMetadata>::new()),
            cached: false,
            cache_path: None,
        };
        EntryMetadataVec::try_from_cache(None).unwrap_or(default)
    }

    /// Attempt to retrieve from cache
    pub fn try_from_cache(cache_path: Option<String>) -> std::io::Result<Self> {
        let cache_path = &cache_path.unwrap_or(DEFAULT_CACHE_PATH.to_string());
        let b = std::fs::read(format!(
            "{}/{}.json",
            cache_path,
            chrono::Utc::now().format("%Y%m%d")
        ));

        match b {
            Ok(b) => {
                let metadata = unsafe {
                    rkyv::from_bytes_unchecked::<Rc<Vec<EntryMetadata>>>(b.as_bytes())
                        .expect("failed to deserialize entry metadata")
                };

                Ok(EntryMetadataVec {
                    inner: metadata,
                    cached: true,
                    cache_path: Some(cache_path.clone()),
                })
            }
            Err(_) => {
                println!("Err: Could not retrieve metadata from cache: {cache_path}, constructing without cache");
                Ok(EntryMetadataVec {
                    inner: Rc::new(Vec::<EntryMetadata>::new()),
                    cached: false,
                    cache_path: None,
                })
            }
        }
    }

    /// Generates a cache file for the metadata, for faster future retrieval
    pub fn to_cache(&mut self, cache_path: Option<String>) -> Option<String> {
        let b = rkyv::to_bytes::<_, 1024>(&self.inner.clone())
            .expect("failed to serialize entry metadata");

        let cache_path = cache_path.unwrap_or(DEFAULT_CACHE_PATH.to_string());

        std::fs::create_dir_all(&cache_path).unwrap_or({
            println!("Could not create directory to cache metadata.");
        });

        let mut cache_path = std::path::PathBuf::from(&cache_path);

        cache_path.push(format!("{}.json", chrono::Utc::now().format("%Y%m%d")));

        let res = std::fs::write(&cache_path, b).ok();

        match res {
            Some(()) => {
                let cache_path = cache_path.to_str().unwrap().to_string();
                self.cache_path = Some(cache_path.clone());
                Some(cache_path)
            }
            None => {
                println!(
                    "Err: could not save cache to {:?}",
                    cache_path.to_str().unwrap()
                );
                None
            }
        }
    }

    fn push(&mut self, e: EntryMetadata) {
        let inner_mut = Rc::get_mut(&mut self.inner).unwrap(); // get mutable reference counter
        inner_mut.push(e);
    }

    pub fn inner(&self) -> &Vec<EntryMetadata> {
        &self.inner
    }

    pub fn sort_by_date(&mut self) {
        let inner_mut = Rc::get_mut(&mut self.inner).unwrap(); // get mutable reference counter
        inner_mut.sort_by(|x, y| x.file_date.cmp(&y.file_date));
    }
}

#[derive(Debug, Clone)]
pub struct AdamTarMetadataExtract {
    pattern: Regex,
    prefix: String,
    pub(crate) tar_path: String,
    pub(crate) entry_metadata: EntryMetadataVec,
    // chained to this struct, because it references entry_metadata
    pub(crate) entry_location_metadata_map: EntryMetadataLocationHash,
}

#[derive(Archive, Serialize, Deserialize, Debug, Clone)]
pub struct EntryMetadata {
    pub raw_file_position: u64,
    pub size: u64,
    pub path: String,
    pub mtime: u64,
    pub file_date: NaiveDate, // date within the filename of each file in the tarball
}

pub trait ExtractTarEntryMetadata {
    fn extract_metadata(&mut self) -> std::io::Result<()>;

    fn add_entry_if_exists(&mut self, location: String) -> bool;
}

impl AdamTarMetadataExtract {
    /// prefix = prefix of object within tarball
    /// NOTE: all data files within tarball assumed to have same prefix
    pub fn new(tar_path: String, prefix: String, metadata_cache_path: Option<String>) -> Self {
        Self {
            // YYYY-mm-dd -> e.g. 2021-09-11 -> DataType::Date32
            // This probably would not work past the year 9999, but if this tool is still being
            // used that far in the future, then we have failed as a species.
            pattern: Regex::new(r"date=(\d{4}-\d{2}-\d{2})/adam.parquet").unwrap(),
            prefix,
            tar_path,
            entry_metadata: match metadata_cache_path {
                Some(p) => EntryMetadataVec::try_from_cache(Some(p))
                    .expect("Failed to extract metadata from cache"),
                None => EntryMetadataVec::new(),
            },
            entry_location_metadata_map: EntryMetadataLocationHash::new(),
        }
    }

    /// File names are not timezone aware, so using NaiveDate
    pub fn construct_locations_from_date_range(start: &NaiveDate, end: &NaiveDate) -> Vec<String> {
        assert!(start <= end);

        {
            let start = &start;
            let end = &end;

            start
                .iter_days()
                .take_while(|x| x <= end)
                .map(|x| format!("date={}/adam.parquet", x.format("%Y-%m-%d")))
                .collect::<Vec<_>>()
        }
    }

    pub fn get_entry_date(path: &String) -> Option<NaiveDate> {
        let re = Regex::new(r"(\d{4}-\d{2}-\d{2})").unwrap();
        match re.captures(path) {
            Some(m) => m[1].parse::<NaiveDate>().ok(),
            _ => None,
        }
    }

    pub fn get_entry(&self, location: String) -> &EntryMetadata {
        self.entry_location_metadata_map
            .inner()
            .get(&location)
            .unwrap()
    }
}

impl ExtractTarEntryMetadata for AdamTarMetadataExtract {
    fn extract_metadata(&mut self) -> std::io::Result<()> {
        println!("----------------------------------------------------------------------------------------------------");
        println!("| >>> loading tar archive >>>");
        println!("----------------------------------------------------------------------------------------------------");
        println!("| archive path = {}", &self.tar_path);

        let mut ta = tar::Archive::new(File::open(&self.tar_path)?);
        ta.entries()?.try_for_each(|e| -> std::io::Result<()> {
            let e = e.expect("corrupt entry");
            let path_str = String::from_utf8(e.path_bytes().to_vec()).unwrap();

            self.entry_metadata.push(EntryMetadata {
                raw_file_position: e.raw_file_position().to_owned(),
                size: e.size().to_owned(),
                path: path_str.to_owned(),
                mtime: e.header().mtime()?.to_owned(),
                file_date: Self::get_entry_date(&path_str).unwrap(),
            });
            Ok(())
        })?;

        self.entry_metadata.sort_by_date();
        Ok(())
    }

    fn add_entry_if_exists(&mut self, location: String) -> bool {
        self.entry_location_metadata_map
            .inner
            .contains_key(&location)
            || {
                let m = &mut self.entry_location_metadata_map;
                let p = &self.pattern;
                let e = &self.entry_metadata;
                let l = &location;
                let pr = &self.prefix;

                p.captures(l).is_some_and(|x| {
                    e.inner().iter().any(|entry| {
                        let exists =
                            entry.path.contains(&x[1].to_string()) && entry.path.contains(pr);
                        if exists {
                            m.insert(location.clone().to_string(), entry.clone());
                        }
                        exists
                    })
                })
            }
    }
}

pub fn print_adam_metadata_stats(metadata: &Vec<EntryMetadata>) {
    println!("----------------------------------------------------------------------------------------------------");
    println!("| >>> tar file stats >>>");
    println!("----------------------------------------------------------------------------------------------------");
    println!("| total entries: {:?}", metadata.len());
    println!(
        "| total size: {:?} mb",
        metadata.iter().map(|x| x.size).sum::<u64>() / 1024 / 1024
    );
    println!(
        "| date range (inferred from filename): {:?} -> {:?}",
        metadata.first().unwrap().file_date,
        metadata.last().unwrap().file_date,
    );
    println!("----------------------------------------------------------------------------------------------------");
}
