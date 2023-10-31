use crate::cli_parser::Cli;
use crate::tar_metadata::AdamTarMetadataExtract;
use crate::tar_object_store::AdamTarFileObjectStore;

use clap::Parser;
use std::io::Write;

pub(crate) mod cli_parser;
pub(crate) mod resampler;
pub(crate) mod tar_metadata;
pub(crate) mod tar_object_store;

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
    );

    resampler::ParquetResampler::resample(adam_resampler.clone()).unwrap();
}

/*
fn main() {
    let locations =
        AdamTarMetadataExtract::construct_locations_from_date_range("2022-01-01", "2022-12-31");

    let tar_path =
        "/home/nvr90/repos/data_engineering/projects/combine_parquet/combpq/blah2020.tar"
            .to_string();

    let prefix = "nowboost/tjl/one_minute_data".to_string();

    let adam_tar_store = AdamTarFileObjectStore::new_with_locations(locations, &tar_path, &prefix);

    std::io::stdout().flush().unwrap();

    let adam_resampler = resampler::ParquetResampler::new(
        adam_tar_store,
        resampler::DataFreq::OneMin,
        resampler::DataFreq::OneHour,
        resampler::FilePartition::ByStation,
        Some(r#"LSD"#.to_string()),
        Some(r#"STN_NUM"#.to_string()),
        Some(vec![
            r#"AIR_TEMP"#.to_string(),
            r#"AIR_TEMP_MIN"#.to_string(),
            r#"AIR_TEMP_MAX"#.to_string(),
            r#"DWPT"#.to_string(),
        ]),
    );

    resampler::ParquetResampler::resample(adam_resampler.clone()).unwrap();
}
*/
