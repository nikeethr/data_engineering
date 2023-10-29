use chrono::prelude::NaiveDate;
use regex::Regex;
use rkyv::{Deserialize, Serialize};
use serde_json;
use std::fs::File;
use std::rc::Rc;
use tar::Archive;

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
}

impl EntryMetadataVec {
    pub fn new() -> Self {
        EntryMetadataVec {
            inner: Rc::new(Vec::<EntryMetadata>::new()),
        }
    }

    /// Generates a cache file for the metadata, for faster future retrieval
    pub fn try_from_cache() -> Self {}

    // pub fn to_cache() -> {

    // }

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

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct EntryMetadata {
    pub raw_file_position: u64,
    pub size: u64,
    pub path: String,
    pub mtime: u64,
    #[serde(default)]
    pub file_date: NaiveDate, // date within the filename of each file in the tarball
}

pub trait ExtractTarEntryMetadata {
    fn extract_metadata(&mut self) -> std::io::Result<()>;

    fn add_entry_if_exists(&mut self, location: String) -> bool;
}

impl AdamTarMetadataExtract {
    /// prefix = prefix of object within tarball
    /// NOTE: all data files within tarball assumed to have same prefix
    pub fn new(tar_path: String, prefix: String) -> Self {
        Self {
            // YYYY-mm-dd -> e.g. 2021-09-11 -> DataType::Date32
            // This probably would not work past the year 9999, but if this tool is still being
            // used that far in the future, then we have failed as a species.
            pattern: Regex::new(r"date=(\d{4}-\d{2}-\d{2})/adam.parquet").unwrap(),
            prefix,
            tar_path,
            entry_metadata: EntryMetadataVec::new(),
            entry_location_metadata_map: EntryMetadataLocationHash::new(),
        }
    }

    /// File names are not timezone aware, so using NaiveDate
    pub fn construct_locations_from_date_range(start: &str, end: &str) -> Vec<String> {
        let start = NaiveDate::parse_from_str(start, "%Y-%m-%d").unwrap();
        let end = NaiveDate::parse_from_str(end, "%Y-%m-%d").unwrap();

        assert!(start <= end);

        {
            let end = &end;
            let start = &start;

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

        let mut ta = Archive::new(File::open(&self.tar_path)?);
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
