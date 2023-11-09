use crate::cli_parser::{Cli, Commands};

use crate::tar_object_store::AdamTarFileObjectStore;

use clap::Parser;
use datafusion::arrow::datatypes::SchemaRef;

use std::io::Write;

pub(crate) mod cli_parser;
pub(crate) mod resampler;
pub(crate) mod schema;
pub(crate) mod tar_metadata;
pub(crate) mod tar_object_store;

/// Sample usage:
///
/// ```
/// ./target/debug/pq_resample
///        --output-freq=one-hour
///        --agg-fields="AIR_TEMP,DWPT"
///        ../combpq/blah2020.tar
///        ./test
///        nowboost/tjl/one_minute_data
/// ```
fn main() {
    let cli = Cli::parse();

    match &cli.command {
        Commands::Resample {
            input_path,
            output_path,
            prefix,
            input_freq,
            output_freq,
            output_format,
            station_field,
            time_field,
            agg_fields,
            schema_ref_path,
            partition_col,
            metadata_cache_path,
            memory_limit_gb,
            worker_threads,
            force_filesystem,
        } => {
            let adam_tar_store = match force_filesystem {
                true => None,
                false => {
                    let adam_tar_store = AdamTarFileObjectStore::new_with_locations(
                        &input_path,
                        &prefix,
                        metadata_cache_path.clone(),
                        None,
                    );
                    tar_metadata::print_adam_metadata_stats(&adam_tar_store.tar_metadata_all);
                    Some(adam_tar_store)
                }
            };

            std::io::stdout().flush().unwrap();
            let adam_resampler = resampler::ParquetResampler::new(
                adam_tar_store,
                input_path.clone(),
                output_path.clone(),
                output_format.clone(),
                input_freq.clone(),
                output_freq.clone(),
                partition_col.clone(),
                Some(time_field.clone()),
                Some(station_field.clone()),
                Some(agg_fields.clone()),
                memory_limit_gb.clone(),
            );

            let schema_ref = match schema_ref_path {
                None => None,
                Some(p) => Some(SchemaRef::new(schema::deserialize(p.clone()).unwrap())),
            };

            resampler::ParquetResampler::resample_async_wrapper(
                adam_resampler,
                worker_threads.clone(),
                schema_ref,
            );
        }

        Commands::InferSchema {
            input_path,
            output_path,
            prefix,
            force_filesystem,
        } => {
            schema::infer_schema_from_first_obj(
                input_path.clone(),
                output_path.clone(),
                prefix.clone(),
                *force_filesystem,
            );
        }
    };
}
