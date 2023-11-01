use crate::cli_parser::Cli;

use crate::tar_object_store::AdamTarFileObjectStore;

use clap::Parser;
use std::io::Write;

pub(crate) mod cli_parser;
pub(crate) mod resampler;
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

    let adam_tar_store = AdamTarFileObjectStore::new_with_locations(
        &cli.input_tar_path,
        &cli.prefix,
        cli.metadata_cache_path,
        None,
    );

    tar_metadata::print_adam_metadata_stats(&adam_tar_store.tar_metadata_all);

    std::io::stdout().flush().unwrap();

    let adam_resampler = resampler::ParquetResampler::new(
        adam_tar_store,
        cli.output_path,
        cli.output_format,
        cli.input_freq,
        cli.output_freq,
        cli.partition_col,
        Some(cli.time_field),
        Some(cli.station_field),
        Some(cli.agg_fields),
        cli.memory_limit_gb,
    );

    resampler::ParquetResampler::resample_async_wrapper(adam_resampler, cli.worker_threads)
}
