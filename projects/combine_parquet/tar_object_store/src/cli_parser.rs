use crate::resampler;
use crate::tar_metadata;
use clap::Parser;

#[derive(Parser)]
#[command(author, version, about, long_about=None, max_term_width=100, color=clap::ColorChoice::Always)]
pub(crate) struct Cli {
    pub(crate) input_tar_path: String,
    pub(crate) output_path: String,
    /// prefix of the directory containing the parquet files within the input tarball.
    pub(crate) prefix: String,

    /// input data interval. Only OneMin is supported as this is the frequency that ADAM outputs at
    /// it can also theoretically support other frequencies assuming they are in a tar archive.
    #[arg(long, value_enum, default_value_t=resampler::DataFreq::OneMin)]
    pub(crate) input_freq: resampler::DataFreq,

    /// frequency of the output data i.e. the interval to aggregate (average) over.
    #[arg(long, value_enum, required = true)]
    pub(crate) output_freq: resampler::DataFreq,

    /// output data format. Note: currently output will always go to a directory.
    /// i.e. the filename cannot be chosen, determined by partition column see: --partition-col.
    #[arg(long, default_value = "parquet", value_names=["parquet", "csv"])]
    pub(crate) output_format: String,

    /// station number column name
    #[arg(long, default_value = "STN_NUM")]
    pub(crate) station_field: String,

    /// observation timestamp column name
    #[arg(long, default_value = "LSD")]
    pub(crate) time_field: String,

    /// the fields to argregate over (average) for each resample time interval. Note: currently does not support
    /// quality flags.
    #[arg(long, required = true)]
    pub(crate) agg_fields: Vec<String>,

    /// column to partition by. Datafusion batching may be faster but will not split output files by station.
    /// recommend using datafusion batching for smaller data output, and station batching for larger outputs.
    #[arg(long, value_enum, default_value_t=resampler::FilePartition::ByStation)]
    pub(crate) partition_col: resampler::FilePartition,

    /// cache a serialized (json) record of the tar file for faster retrieval
    #[arg(long, default_value = tar_metadata::DEFAULT_CACHE_PATH)]
    pub(crate) metadata_cache_path: Option<String>,
}
