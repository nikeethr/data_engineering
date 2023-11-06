use datafusion::arrow::record_batch::RecordBatch;
use datafusion::dataframe::DataFrame;
use datafusion::prelude::*;
use datafusion::arrow::downcast_primitive_array;


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
const PQ_EXTENSIONS: [&'static str; 2] = [".pq", ".parquet"];
const CSV_EXTENSIONS: [&'static str; 1] = [".csv"];

struct DfQuerier {
    input_path: String,
    output_path: Option<String>,
    /// for simplicity input format = output format, i.e. no conversion
    /// TODO: if there's enough demand we can add conversion, for now the in-memory option exists
    /// to retrieve the raw records and save to csv via python libs like pandas.
    data_format: Option<String>,
}

/// Actual rust thingy that does the querying
impl DfQuerier {
    pub fn new_from_data_dir(input_path: String) -> Self {
        DfQuerier {
            input_path,
            output_path: None,
            data_format: None,
        }
    }

    fn with_output_path(mut self, path: String) -> Self {
        self.output_path = Some(path);
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

    /// Runs the datafusion query in rust using async threads/parallel execution
    /// Returns None if saving to file, otherwise collect and return in-memory records
    fn run_df_query(self, query: String) -> Option<HashMap<String, dyn Array>> {
        self.verify(query);

        tokio::runtime::Builder::build().block_on(async move {
            // execute

            // if in-memory -> return result
            // -> iterate through RecordBatches or StreamingRecordBatch
            // -> get col metadata/field/name for each record 
            // -> create hashmap and downcast (invistigate if downcast needed)
            // -> if downcast needed, we may need to create our own generic type
            // May need custom casting e.g.:
            // {
            //     let column =
            //         batchs[0].column_by_name(field.name()).unwrap();
            //     if field.data_type().is_numeric() {
            //         cast(column, &DataType::Float64)?
            //     } else {
            //         cast(column, &DataType::Utf8)?
            //     }
            // }
            // _ => Arc::new(StringArray::from(vec!["null"])),
            //
            // Then back down to primitive type based on data_type
            // For now we can have:
            // - FloatArray
            // - IntArray
            // - StringArray
            result

            // else save output to file and return None
            None
        });

    }

    fn verify(&self, query: String) {
        // check necessary inputs are not None

        // check that the query string is okay using datafusion
    }
}

/// Wrapper around run_df_query to handle type conversions
/// Args:
///   > q = query
///   > data_dir = path to the data directory containing dataframe
///   > data_format = currently supports .parquet/.pq or .csv
///   > output_path = optional path to output the data to
#[pyfunction]
fn py_run_df_query(
    q: &str,
    data_dir: &str,
    data_format: &str,
    output_path: Option<&str>,
) -> PyResult<PyAny> {
    let df_querier = DfQuerier::new_from_data_dir(data_dir)
        .with_output_path(output_path.into_string())
        .with_data_format(data_format.into_string());
    df_querier = builder.build();

    // returns Some(Records) or None if it saves to disk
    df_querier.run_df_query(q)
}

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(a: usize, b: usize) -> PyResult<String> {
    Ok((a + b).to_string())
}

/// A Python module implemented in Rust.
#[pymodule]
fn pydf(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_run_df_query, m)?)?;
    Ok(())
}
