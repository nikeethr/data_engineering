mod common {
    /// -------------------------------------------------------------------------------------------
    /// common date/time operations
    /// -------------------------------------------------------------------------------------------
    use std::cmp::{Ordering, PartialOrd};
    use sysinfo::{System, SystemExt};

    /// how much data a file contains - e.g.
    /// DAY => files are named by `*YYYY-MM-DD*` and hence contain a day's worth of data
    /// MONTH => files are named by month i.e. `MM-DD*`
    /// NOTE: In this definition, a file is a *.parquet/*.pq extension
    #[derive(Debug, Clone, PartialOrd, PartialEq)]
    pub enum FileFreq {
        Daily,
        Monthly,
        Yearly,
        SingleFile,
    }

    /// the frequency of data of the input data e.g. OneMin => each entry in the source file is by
    /// minute, currently limiting to certain options, but this can be made generic in the future
    /// in the meantime CustomFreqSeconds can be used, but requires implementation of to_seconds()
    /// see:  [`Seconds`]
    #[derive(Debug, Clone)]
    pub enum DataFreq {
        OneMin,
        TenMins,
        OneHour,
        CustomFreqSeconds(SecondsType),
    }

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

    /// Also implicitly implements [`Into<SecondsType>`]
    impl From<DataFreq> for Seconds {
        fn from(s: DataFreq) -> Seconds {
            match s {
                DataFreq::OneMin => Seconds(60),
                DataFreq::TenMins => Seconds(60 * 10),
                DataFreq::OneHour => Seconds(60 * 60),
                DataFreq::CustomFreqSeconds(inner) => Seconds(inner),
            }
        }
    }

    /// -------------------------------------------------------------------------------------------
    /// system info
    /// -------------------------------------------------------------------------------------------
    pub fn get_available_reserve_memory() -> u64 {
        let mut sys = System::new_all();
        sys.refresh_all();
        const RESERVE_FACTOR: f64 = 0.2; // amount of memory to reserve
        sys.available_memory() - ((sys.total_memory() as f64 * RESERVE_FACTOR) as u64)
    }

    // TODO: probably split tests with macro
    #[test]
    fn test_cmp_seconds() {
        assert_eq!(
            Seconds::from(DataFreq::TenMins) >= Seconds::from(DataFreq::CustomFreqSeconds(6)),
            false
        );

        assert_eq!(
            Seconds::from(DataFreq::OneHour) >= Seconds::from(DataFreq::OneMin),
            true
        );
    }

    #[test]
    fn test_get_available_reserve_memory() {
        let mut sys = System::new_all();
        sys.refresh_all();
        assert!(get_available_reserve_memory() < sys.available_memory());
        // purely a sanity check:
        // we should have reasonable enough memory to run tests
        // otherwise this would fail anyway
        assert!(get_available_reserve_memory() > (sys.available_memory() as f64 * 0.01) as u64);
    }
}

mod intermediate_store {
    use async_trait::async_trait;
    /// This module is currently only useful for a tar archives, since parquet lib cannot read
    /// directly from them. Only supports uncompressed .tar archives. Parquet files are
    /// efficiently compressed anyways, so it's potentially a waste to compress it again, so
    /// .tar.gz are not suppoprted... for now
    use object_store::{path::Path as ObjPath, ObjectStore};
    use tokio::io::Result;

    /// probably could have inferred the object store type via implementing generics
    /// but being explicit for now...
    pub enum IntermediateStoreType {
        InMemory,
        LocalFileSystem,
    }

    // NOTE: ObjPath::from_filesystem_path
    #[async_trait]
    pub trait IntermediateStore {
        async fn into_intermediate_store(&self, store_type: IntermediateStoreType) -> Result<()>;
    }
}

mod parquet_table_reader {
    use super::intermediate_store::{IntermediateStore, IntermediateStoreType};
    use async_trait::async_trait;
    use datafusion::prelude::{ParquetReadOptions, SessionContext};
    use object_store::{path::Path as ObjPath, ObjectStore};
    use std::path::Path as FilePath;
    use tokio::io::Result;

    enum DataSource {
        FileSystem,
        Tarball,
    }

    /// Generic trait to register a table to a given context
    /// Currently only supports registering a table, it could potentially also be used to read as a
    /// dataframe for spark/pandas like map-reduce operations.
    #[async_trait]
    trait ParquetTableReader {
        async fn register_table(&self) -> datafusion::error::Result<()>; // TODO: may require result
    }

    /// Generic trait to read input tarball
    #[async_trait]
    trait TarballReader {}

    struct TableReaderInfo<'a> {
        pub file_path: &'a FilePath,
        pub parquet_ext: String,
        pub table_name: String,
    }
    /// registers a directory of parquet files for reading
    struct ParquetFileSystemTableReader<'a> {
        ctx: &'a SessionContext,
        reader_info: TableReaderInfo<'a>,
    }

    struct ParquetTarTableReader<'a> {
        ctx: &'a SessionContext,
        reader_info: TableReaderInfo<'a>,
        intermediate_obj_path: ObjPath,
    }

    /// registers table for directory in a filesystem
    #[async_trait]
    impl<'a> ParquetTableReader for ParquetFileSystemTableReader<'a> {
        async fn register_table(&self) -> datafusion::error::Result<()> {
            let mut parquet_options = ParquetReadOptions::default();
            parquet_options.file_extension = self.reader_info.parquet_ext.as_str();
            self.ctx
                .register_parquet(
                    &self.reader_info.table_name,
                    self.reader_info.file_path.to_str().unwrap(),
                    parquet_options,
                )
                .await?;
            Ok(())
        }
    }

    #[async_trait]
    impl IntermediateStore for ParquetTarObjectStore<LocalFileSystem> {
        async fn to_intermediate<LocalFileSystem>(
            &self,
            path: Arc<ObjStorePath>,
            entry: Arc<EntryMetadata>,
        ) -> Result<()> {
            let archive_path = self.archive_path.to_owned();
            let obj_path = path.to_owned();

            tokio::task::spawn_blocking(move || -> Result<()> {
                // bypass object store api since it's probably not efficient
                let f = File::open(archive_path)?;
                let f_out = File::open(obj_path.to_string())?;
                let r = &mut BufReader::new(f);
                let w = &mut BufWriter::new(f_out);
                r.seek(SeekFrom::Start(entry.raw_file_position))?;
                r.take(entry.size);
                std::io::copy(r, w)?;
                w.flush()
            })
            .await?
        }
    }

    #[async_trait]
    impl<T> TarToObjectStore for ParquetTarObjectStore<T>
    where
        T: ObjectStore,
        ParquetTarObjectStore<T>: IntermediateStore,
    {
        type TarFileFilter = fn(&Path) -> bool;

        async fn read_entries(&self, filter: Option<Self::TarFileFilter>) -> tokio::io::Result<()> {
            let entries =
                tokio::task::block_in_place(move || -> std::io::Result<Vec<EntryMetadata>> {
                    let mut ta = Archive::new(File::open(&self.archive_path)?);
                    let res = ta
                        .entries()?
                        .map(|e| -> tokio::io::Result<EntryMetadata> {
                            let e = e.expect("corrupt entry");
                            if let Some(f) = filter {
                                if !f(e.path()?.as_ref()) {
                                    return Err(Error::from(ErrorKind::NotFound));
                                }
                            }
                            Ok(EntryMetadata {
                                raw_file_position: e.raw_file_position(),
                                size: e.size(),
                                path: Arc::new(e.path()?.to_path_buf()),
                            })
                        })
                        .filter_map(|e| e.ok())
                        .collect::<Vec<_>>();
                    Ok(res)
                });

            for e in entries? {
                self.to_intermediate::<T>(
                    ObjStorePath::parse(&self.obj_store_path).unwrap().into(),
                    e.into(),
                )
                .await?;
            }

            Ok(())
        }
    }

    /// registers table through intermediate store for tarball
    #[async_trait]
    impl<'a> ParquetTableReader for ParquetTarTableReader<'a> {
        async fn register_table(&self) -> datafusion::error::Result<()> {
            todo!()
        }
    }

    #[async_trait]
    impl<'a> IntermediateStore for ParquetTarTableReader<'a> {
        async fn into_intermediate_store(&self, store_type: IntermediateStoreType) -> Result<()> {
            // read tar file entries
            match store_type {
                IntermediateStoreType::InMemory => {}
                IntermediateStoreType::LocalFileSystem => {}
            }
        }
    }

    impl<'a> ParquetTarTableReader<'a> {
        type TarFileFilter = fn(&Path) -> bool;

        async fn read_entries(&self, filter: Option<T>) -> tokio::io::Result<()> {
            let entries =
                tokio::task::block_in_place(move || -> std::io::Result<Vec<EntryMetadata>> {
                    let mut ta = Archive::new(File::open(&self.archive_path)?);
                    let res = ta
                        .entries()?
                        .map(|e| -> tokio::io::Result<EntryMetadata> {
                            let e = e.expect("corrupt entry");
                            if let Some(f) = filter {
                                if !f(e.path()?.as_ref()) {
                                    return Err(Error::from(ErrorKind::NotFound));
                                }
                            }
                            Ok(EntryMetadata {
                                raw_file_position: e.raw_file_position(),
                                size: e.size(),
                                path: Arc::new(e.path()?.to_path_buf()),
                            })
                        })
                        .filter_map(|e| e.ok())
                        .collect::<Vec<_>>();
                    Ok(res)
                });

            for e in entries? {
                self.to_intermediate::<T>(
                    ObjStorePath::parse(&self.obj_store_path).unwrap().into(),
                    e.into(),
                )
                .await?;
            }

            Ok(())
        }
    }
}


/// Obj store:
///
/// Note: registering can be done in common function (e.g. trait, or separate function - probably
/// easier to use separate function)
///
/// 1. register_object_store to register the store:
/// e.g.
///
/// How do we prompt rust to only read when required????
///
/// 2. register_listing_table to register the table to the object store
///
