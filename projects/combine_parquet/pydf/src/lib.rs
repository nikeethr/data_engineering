#[macro_use]
extern crate approx;

use crate::stats::*;

use datafusion::arrow::array::{
    Array, ArrayRef, BooleanArray, Float64Array, Int64Array, StringArray, TimestampNanosecondArray,
};

use datafusion::execution::runtime_env::{RuntimeConfig, RuntimeEnv};

use datafusion::arrow::datatypes::{DataType, Schema};

use datafusion::arrow::record_batch::{RecordBatch, RecordBatchIterator};
use datafusion::dataframe::DataFrameWriteOptions;
use datafusion::execution::disk_manager::DiskManagerConfig;
use datafusion::execution::memory_pool::FairSpillPool;
use datafusion::execution::object_store::DefaultObjectStoreRegistry;

use datafusion::prelude::*;
use log::info;

use std::collections::HashMap;
use std::sync::Arc;
use sysinfo::{System, SystemExt};

use pyo3::{exceptions::PyNotImplementedError, prelude::*};

use numpy::PyArray1;

mod stats;

const SUPPORTED_FORMATS: [&'static str; 2] = ["parquet", "csv"];

// -------------------------------------------------------------------------------------------------
// >>> Downcast helpers: datafusion types -> arrow primitive types -> native types
// -------------------------------------------------------------------------------------------------

macro_rules! to_pydf {
    ($i:ident, $t:ty, $u:expr) => {
        Arc::new(
            $i.as_any()
                .downcast_ref::<$t>()
                .unwrap()
                .iter()
                .map(|x| $u(x.force_default().unwrap().into()))
                .collect::<Vec<_>>(),
        )
    };
}

macro_rules! force_default_opt {
    ($t:ty, $e:expr) => {
        impl ForceDefaultOpt for Option<$t> {
            fn force_default(self) -> Self {
                self.or(Some($e))
            }
        }
    };
}

#[derive(Clone)]
enum PyElem {
    Bool(bool),
    Str(String),
    Int(i64),
    Float(f64),
    Timestamp(i64),
}

pub trait ForceDefaultOpt {
    fn force_default(self: Self) -> Self;
}
force_default_opt!(f64, f64::NAN);
force_default_opt!(i64, i64::MIN);
force_default_opt!(String, "NA".to_string());
force_default_opt!(&str, "NA");
force_default_opt!(bool, false);

impl IntoPy<PyObject> for PyElem {
    fn into_py(self, py: Python<'_>) -> PyObject {
        match self {
            Self::Bool(val) => val.into_py(py),
            Self::Str(val) => val.into_py(py),
            Self::Int(val) => val.into_py(py),
            Self::Float(val) => val.into_py(py),
            Self::Timestamp(val) => val.into_py(py),
        }
    }
}

#[pyclass]
struct PyDfDictWrapper {
    #[pyo3(get)]
    inner: Option<HashMap<String, Vec<PyElem>>>,
}

type PyDfDict = Option<HashMap<String, Vec<PyElem>>>;

fn pyconvert(a: &ArrayRef) -> Arc<Vec<PyElem>> {
    let t = a.data_type();
    if t.equals_datatype(&DataType::Boolean) {
        to_pydf!(a, BooleanArray, PyElem::Bool)
    } else if t.equals_datatype(&DataType::Utf8) {
        to_pydf!(a, StringArray, PyElem::Str)
    } else if t.is_integer() {
        to_pydf!(a, Int64Array, PyElem::Int)
    } else if t.is_floating() {
        to_pydf!(a, Float64Array, PyElem::Float)
    } else if t.is_temporal() {
        // Represent as string array, since we may want time before unix epoch, otherwise
        // defaults to timestamp64
        // TODO: check if this actually works, or a manual cast is required.
        to_pydf!(a, TimestampNanosecondArray, PyElem::Timestamp)
    } else {
        unimplemented!()
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
        schema: Option<&Schema>,
        ctx: &SessionContext,
    ) -> tokio::io::Result<()> {
        if let Some(f) = &self.data_format {
            match f.as_str() {
                "csv" => {
                    let options = match schema {
                        Some(s) => CsvReadOptions::default().schema(s),
                        None => CsvReadOptions::default(),
                    };
                    ctx.register_csv(name, path, options).await?
                }
                "parquet" => {
                    let options = match schema {
                        Some(s) => ParquetReadOptions::default().schema(s),
                        None => ParquetReadOptions::default(),
                    };
                    ctx.register_parquet(name, path, options.parquet_pruning(true))
                        .await?
                }
                &_ => unreachable!(), // format is verified before this point
            }
        }
        Ok(())
    }

    fn convert_records_to_pydf(&self, record_batches: Vec<RecordBatch>) -> PyDfDict {
        let mut pydf_dict = HashMap::new();

        let schema_ref = record_batches.first().unwrap().schema().clone();

        let record_batch_iter =
            RecordBatchIterator::new(record_batches.into_iter().map(Ok), schema_ref);

        record_batch_iter.filter_map(|b| b.ok()).for_each(|b| {
            assert_eq!(b.schema().fields().len(), b.num_columns());
            for i in 0..b.num_columns() {
                let pydf_dict = &mut pydf_dict;
                let field_name = b.schema().fields.get(i).unwrap().name().to_owned();
                let col = b.column_by_name(field_name.as_str()).unwrap();
                if pydf_dict.contains_key(&field_name) {
                    if let Some(v) = pydf_dict.get_mut(&field_name) {
                        let mut v = v;
                        let col_exist: &mut Vec<PyElem> = Arc::get_mut(&mut v).unwrap();
                        // we no longer need this
                        let col_insert = Arc::into_inner(pyconvert(col)).unwrap();
                        col_exist.extend(col_insert.into_iter());
                    }
                } else {
                    pydf_dict.insert(field_name.clone(), pyconvert(col));
                }
            }
        });

        // extract out of Arc, as we will need extact types
        let mut pydf_dict_solid = HashMap::new();
        pydf_dict.into_iter().for_each(|(k, v)| {
            pydf_dict_solid.insert(k, Arc::into_inner(v).unwrap());
        });

        Some(pydf_dict_solid)
    }

    /// Runs the datafusion query in rust using async threads/parallel execution
    ///
    /// Returns None if saving to file, otherwise collect and return in-memory records
    ///
    /// TODO: break this up into separate functions
    fn run_df_query(&self, query: &str) -> PyDfDict {
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

                info!(">>> Register input table");
                self.register_table_helper(&self.input_table_name, &self.input_path, None, &ctx)
                    .await
                    .expect("Could not register input table");

                info!(">>> perform query");
                // this is the main part that uses async io
                let df = ctx.sql(query).await.expect("failed to execute query");

                let res = match self.output_path.clone() {
                    Some(p) => {
                        info!(">>> Output to file: {:?}", &self.output_path);
                        info!("register table: {:?}", &self.output_table_name);
                        self.register_table_helper(
                            &self.output_table_name,
                            p.as_str(),
                            Some(&df.schema().into()),
                            &ctx,
                        )
                        .await
                        .expect("unable to write output");
                        df.clone()
                            .write_table(&self.output_table_name, DataFrameWriteOptions::default())
                            .await
                            .expect("unable to write dataframe");
                        None
                    }
                    None => {
                        // return dataframe in memory or print preview
                        if self.preview_only {
                            info!(">>> Previewing data");
                            df.clone().show_limit(10).await.unwrap();
                            None
                        } else {
                            info!(">>> In-memory table");
                            self.convert_records_to_pydf(df.clone().collect().await.unwrap())
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
fn pydf_run_query<'py>(
    q: &'py str,
    input_path: &'py str,
    input_table_name: &'py str,
    data_format: &'py str,
    preview_only: bool,
    output_path: Option<&'py str>,
    output_table_name: Option<&'py str>,
) -> PyResult<PyDfDictWrapper> {
    let df_querier = DfQuerier::new_from_data_dir(input_path, input_table_name)
        .with_output_path(output_path, output_table_name)
        .with_data_format(data_format)
        .with_preview_only(preview_only);

    // returns Some(Records) or None if it saves to disk
    let res = df_querier.run_df_query(q);
    Ok(PyDfDictWrapper { inner: res })
}

#[pyfunction]
fn pydf_kurtosis_1d<'py>(a: &'py PyArray1<f64>) -> PyResult<f64> {
    Ok(kurtosis_1d(&a.to_vec().unwrap()))
}

#[pyfunction]
fn pydf_skewness_1d<'py>(a: &PyArray1<f64>) -> PyResult<f64> {
    Ok(skewness_1d(&a.to_vec().unwrap()))
}

#[pyfunction]
fn pydf_hist_1d<'py>(a: &PyArray1<f64>, bins: u64) -> PyResult<Vec<(f64, f64, u64)>> {
    Ok(hist_1d(&a.to_vec().unwrap(), bins))
}

#[pyfunction]
fn pydf_yj_correction_1d<'py>(a: &PyArray1<f64>, lambda: f64) -> PyResult<Vec<f64>> {
    Ok(yeo_johnson_1d(Arc::new(&a.to_vec().unwrap()), lambda))
}

#[pyfunction]
fn pydf_yj_optimize<'py>(a: &PyArray1<f64>) -> PyResult<((f64, f64), (f64, f64))> {
    Ok(yeo_johnson_1d_power_correction(&a.to_vec().unwrap()))
}

/// A Python module implemented in Rust.
#[pymodule]
fn pydf(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(pydf_run_query, m)?)?;
    m.add_function(wrap_pyfunction!(pydf_kurtosis_1d, m)?)?;
    m.add_function(wrap_pyfunction!(pydf_skewness_1d, m)?)?;
    m.add_function(wrap_pyfunction!(pydf_hist_1d, m)?)?;
    m.add_function(wrap_pyfunction!(pydf_yj_optimize, m)?)?;
    m.add_function(wrap_pyfunction!(pydf_yj_correction_1d, m)?)?;
    m.add_class::<PyDfDictWrapper>()?;
    Ok(())
}
