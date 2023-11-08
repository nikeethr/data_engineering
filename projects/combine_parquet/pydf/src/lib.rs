use datafusion::arrow::array::{
    cast, Array, ArrayAccessor, ArrayRef, BooleanArray, Date64Array, Float64Array, Int64Array,
    PrimitiveArray, StringArray,
};

use datafusion::datasource::listing::ListingOptions;
use datafusion::execution::runtime_env::{RuntimeConfig, RuntimeEnv};

use datafusion::arrow::compute::lexicographical_partition_ranges;
use datafusion::arrow::datatypes::{ArrowPrimitiveType, DataType};
use datafusion::arrow::downcast_primitive_array;
use datafusion::arrow::record_batch::{RecordBatch, RecordBatchIterator};
use datafusion::dataframe::{DataFrame, DataFrameWriteOptions};
use datafusion::execution::disk_manager::DiskManagerConfig;
use datafusion::execution::memory_pool::FairSpillPool;
use datafusion::execution::object_store::{DefaultObjectStoreRegistry, ObjectStoreRegistry};
use datafusion::prelude::*;
use log::{info, warn};
use std::any::Any;
use std::collections::HashMap;
use std::sync::{Arc, Weak};
use sysinfo::{System, SystemExt};

// for parsing sql
// use datafusion::sql::sqlparser
use pyo3::{exceptions::PyNotImplementedError, prelude::*};

// TODO:
// [ ] API input - output compatibility
// [x] GIL unlock - not needed unless we explicitly want to use python threads or are writting the main function cli
// [ ] Datafusion query
// [ ] Python module init
// [ ] Example code
// [ ] Docs

const SUPPORTED_FORMATS: [&'static str; 2] = ["parquet", "csv"];

// -------------------------------------------------------------------------------------------------
// >>> Downcast helpers: datafusion types -> arrow primitive types -> native types
// -------------------------------------------------------------------------------------------------

macro_rules! to_pydf {
    ($i:ident, $t:ty, $u:ty) => {
        Arc::new(PyDfArrayWrapper::<$u>::new(
            $i.as_any()
                .downcast_ref::<$t>()
                .unwrap()
                .iter()
                .map(|x| Box::new(x.unwrap().into()))
                .collect::<Vec<$u>>(),
        )) as Arc<dyn PyDfArray<PyElem = $u>>
    };
}

trait PyDfArray: DynPyDfArray + Extend {
    fn as_extend(&self ) -> Extend
}

trait PyDfArray {
    fn extend(self: &mut Self, other: Arc<dyn PyDfArray>);
}

struct PyDfArrayWrapper<T> {
    /// we may share the vector across threads, but we may only process the vector within the thread
    inner: Arc<Vec<T>>,
}

impl<T> PyDfArrayWrapper<T> {
    pub fn new(a: Arc<Vec<T>>) -> Self {
        PyDfArrayWrapper::<T> { inner: a }
    }

    fn pyconvert(&self, a: ArrayRef) -> Arc<dyn PyDfArray> {
        let t = a.data_type();
        if t.equals_datatype(&DataType::Boolean) {
            to_pydf!(a, BooleanArray, bool)
        } else if t.equals_datatype(&DataType::Utf8) {
            to_pydf!(a, StringArray, String)
        } else if t.is_integer() {
            to_pydf!(a, Int64Array, i64)
        } else if t.is_floating() {
            to_pydf!(a, Float64Array, f64)
        } else if t.is_temporal() {
            // Represent as string array, since we may want time before unix epoch, otherwise
            // defaults to timestamp64
            // TODO: check if this actually works, or a manual cast is required.
            to_pydf!(a, StringArray, String)
        } else {
            unimplemented!()
        }
    }
}

impl<T> PyDfArray for PyDfArrayWrapper<T> {
    type PyElem = T;
    fn extend(&mut self, other: ArrayRef) {
        let this = Arc::get_mut(&mut self.inner).unwrap();
        this.extend(self.pyconvert(other).inner());
    }

    fn inner(&mut self) -> Arc<Vec<Self::PyElem>> {
        self.inner
    }
}

// -------------------------------------------------------------------------------------------------
// >>> Hook into datafusion api to perform the query
// -------------------------------------------------------------------------------------------------

struct DfQuerier {
    /// Note: this can take in a glob expression
    input_path: String,
    input_table_name: String,
    output_path: Option<String>,
    output_table_name: String,
    /// Defaults to Parquet
    /// for simplicity input format = output format, i.e. no conversion
    /// TODO: if there's enough demand we can add conversion, for now the in-memory option exists
    /// to retrieve the raw records and save to csv via python libs like pandas.
    data_format: Option<String>,
    preview_only: bool,
}

/// Actual rust thingy that does the querying
impl DfQuerier {
    pub fn new_from_data_dir(input_path: &str, input_table_name: &str) -> Self {
        DfQuerier {
            input_path: input_path.to_string(),
            input_table_name: input_table_name.to_string(),
            output_path: None,
            data_format: None,
            output_table_name: "output_table".to_string(),
            preview_only: false,
        }
    }

    fn with_output_path(mut self, path: Option<&str>, name: Option<&str>) -> Self {
        self.output_path = path.map(|p| p.to_string());
        self.output_table_name = name.unwrap_or("output_table").to_string();
        self
    }

    fn with_preview_only(mut self, preview: bool) -> Self {
        self.preview_only = preview;
        self
    }

    fn with_data_format(mut self, data_format: &str) -> Self {
        let supported = SUPPORTED_FORMATS
            .as_ref()
            .iter()
            .any(|f| data_format.eq_ignore_ascii_case(f));
        if !supported {
            PyNotImplementedError::new_err("Unsupported format.");
            unimplemented!();
        }
        self.data_format = Some(data_format.to_string());
        self
    }

    async fn register_table_helper(
        &self,
        name: &str,
        path: &str,
        ctx: &SessionContext,
    ) -> tokio::io::Result<()> {
        if let Some(f) = &self.data_format {
            match f.as_str() {
                "csv" => {
                    ctx.register_csv(name, path, CsvReadOptions::default())
                        .await?
                }
                "parquet" => {
                    ctx.register_parquet(name, path, ParquetReadOptions::default())
                        .await?
                }
                &_ => unreachable!(), // format is verified before this point
            }
        }
        Ok(())
    }

    async fn register_io_tables(&self, ctx: &SessionContext) -> tokio::io::Result<()> {
        info!("register table: input");
        self.register_table_helper(&self.input_table_name, &self.input_path, &ctx)
            .await?;

        match &self.output_path {
            None => {
                info!("output is in-memory -> returns a in memory dictionary");
            }
            Some(p) => {
                info!("register table: output");
                self.register_table_helper(&self.output_table_name, p, &ctx)
                    .await?;
            }
        };
        Ok(())
    }

    fn convert_records_to_pydf<T>(record_batches: Vec<RecordBatch>) -> PyDfDictOpt
    where
        T: Sync + Send,
    {
        let mut pydf_dict = HashMap::new();

        let record_batch_iter = RecordBatchIterator::new(
            record_batches.into_iter().map(Ok),
            record_batches.first().unwrap().schema(),
        );

        record_batch_iter.filter_map(|b| b.ok()).for_each(|b| {
            assert_eq!(b.schema().fields().len(), b.num_columns());
            for i in 0..b.num_columns() {
                let mut pydf_dict = &mut pydf_dict;
                let field_name = b.schema().fields.get(i).unwrap().name();
                let col = b.column_by_name(field_name.as_str()).unwrap();
                let col = to_pydf_generic!(col);
                if pydf_dict.contains_key(field_name) {
                    if let Some(v) = pydf_dict.get_mut(field_name) {
                        let mut col_exist = Arc::get_mut(v).unwrap();
                    }
                } else {
                    pydf_dict.insert(field_name.to_string(), col);
                }
            }
        });

        Some(pydf_dict)
    }

    /// Runs the datafusion query in rust using async threads/parallel execution
    ///
    /// Returns None if saving to file, otherwise collect and return in-memory records
    ///
    /// TODO: break this up into separate functions
    fn run_df_query(&self, query: &str) -> PyDfDictOpt {
        self.verify(query);

        tokio::runtime::Builder::new_multi_thread()
            .build()
            .unwrap()
            .block_on(async move {
                // --- create runtime environment ---
                info!(">>> Create runtime environment");
                let rt = RuntimeConfig::new();

                info!("register disk manager: assigned by OS usually in /tmp/");
                let rt = rt.with_disk_manager(DiskManagerConfig::new());

                info!("initialize object store registry: filesystem");
                // this includes the local filesystem by default so we only need to
                // register the tar store
                let rt = rt.with_object_store_registry(Arc::new(DefaultObjectStoreRegistry::new()));

                info!("register memory pool: with diskspill @ 80% of max memory");
                let mut sys = System::new_all();
                sys.refresh_all();
                let mem_avail = sys.available_memory() as usize;
                let mem_avail_frac = (mem_avail as f64 * 0.8) as usize;
                let rt = rt.with_memory_pool(Arc::new(FairSpillPool::new(mem_avail_frac)));

                info!(">>> Enter datafusion session");
                let ctx = SessionContext::new_with_config_rt(
                    SessionConfig::new(),
                    Arc::new(RuntimeEnv::new(rt).expect("Could not create runtime env")),
                );

                info!(">>> Register io tables");
                self.register_io_tables(&ctx)
                    .await
                    .expect("Could not register tables");

                info!(">>> perform query");
                // this is the main part that uses async io
                let df = ctx.sql(query).await.expect("failed to execute query");

                let res = match self.output_path {
                    Some(p) => {
                        df.clone()
                            .write_table(&self.output_table_name, DataFrameWriteOptions::default());
                        None
                    }
                    None => {
                        // return dataframe in memory or print preview
                        if self.preview_only {
                            df.clone().show_limit(10).await?;
                            None
                        } else {
                            self.convert_records_to_pydf(df.clone().collect().await?)
                        }
                    }
                };
                res
            })
    }

    fn verify(&self, query: &str) {
        // check that the query string is okay using datafusion
        let parsed = datafusion::sql::parser::DFParser::parse_sql(query)
            .expect("Could not parse sql statements.");
        println!("--- parsed sql statements ---");
        println!("{:?}", parsed);
        println!("---");
    }
}

/// Wrapper around run_df_query to handle type conversions
/// Args:
///   > q = query
///   > input_path = path to the data directory containing dataframe
///   > data_format = currently supports .parquet/.pq or .csv
///   > output_path = optional path to output the data to
#[pyfunction]
fn pydf_run_query(
    q: &str,
    input_path: &str,
    input_table_name: &str,
    data_format: &str,
    preview_only: bool,
    output_path: Option<&str>,
    output_table_name: Option<&str>,
) -> PyResult<PyDfDictOptWrapper> {
    let df_querier = DfQuerier::new_from_data_dir(input_path, input_table_name)
        .with_output_path(output_path, output_table_name)
        .with_data_format(data_format)
        .with_preview_only(preview_only);

    // returns Some(Records) or None if it saves to disk
    let res = df_querier.run_df_query(q);
    Ok(PyDfDictOptWrapper(res))
}

/// A Python module implemented in Rust.
#[pymodule]
fn pydf(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(pydf_run_query, m)?)?;
    Ok(())
}
