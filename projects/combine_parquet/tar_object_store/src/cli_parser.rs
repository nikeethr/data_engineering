use crate::resampler;
use crate::tar_metadata;

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(author, version, about, long_about=None, max_term_width=100, color=clap::ColorChoice::Always)]
#[command(propagate_version = true)]
pub(crate) struct Cli {
    #[command(subcommand)]
    pub(crate) command: Commands,
}

#[derive(Subcommand)]
pub(crate) enum Commands {
    /// Performs resampling (i.e. downsampling over time dimension) of the input tar+pq object store
    /// into parquet or csv outputs.

    /// Note:
    /// * Currently only supports parquet format as input, and json as output.
    /// * You can force the tool to get data from a raw parquet file instead of a tar archive by
    ///   using the force-fileystem flag. In this case, input_path will be a directory of parquet
    ///   files  instead.
    Resample {
        /// path to the input data. Note: by default this is a tar archive, but you can force to
        /// refer to a local filesystem using --force-filesystem option. Note by default the purpose
        /// of this tool is to resample data from tar formats, it may be better to use datafusion
        /// directly for general purposes.
        input_path: String,
        /// path to output data, currently only supports a local file system.
        output_path: String,
        /// prefix of the directory containing the parquet files within the input tarball.
        prefix: String,

        /// input data interval. Only OneMin is supported as this is the frequency of ADAM obs.
        /// It can also theoretically support other frequencies assuming they are in a tar
        /// archive.
        #[arg(long, value_enum, default_value_t=resampler::DataFreq::OneMin)]
        input_freq: resampler::DataFreq,

        /// frequency of the output data i.e. the interval to aggregate (average) over.
        #[arg(long, value_enum, required = true)]
        output_freq: resampler::DataFreq,

        /// output data format. Note: currently output will always go to a directory.
        /// i.e. the filename cannot be chosen, determined by partition column see: --partition-col.
        #[arg(long, value_enum, default_value_t = resampler::OutputFormat::Parquet)]
        output_format: resampler::OutputFormat,

        /// station number column name
        #[arg(long, default_value = "STN_NUM")]
        station_field: String,

        /// observation timestamp column name
        #[arg(long, default_value = "LSD")]
        time_field: String,

        /// the fields to argregate over (average) for each resample time interval. Note: currently
        /// does not support quality flags.
        #[arg(long, required = true, value_delimiter = ',')]
        agg_fields: Vec<String>,

        #[arg(long, default_value = None)]
        schema_ref_path: Option<String>,

        /// column to partition by. Datafusion batching may be faster but will not split output
        /// files by station. recommend using datafusion batching for smaller data output, and
        /// station batching for larger outputs.
        #[arg(long, value_enum, default_value_t=resampler::FilePartition::ByStation)]
        partition_col: resampler::FilePartition,

        /// cache a serialized (json) record of the tar file for faster retrieval
        #[arg(long, default_value = tar_metadata::DEFAULT_CACHE_PATH)]
        metadata_cache_path: Option<String>,

        /// soft memory limit to limit queries to, note: the tool tries to keep under 80% of the
        /// provided memory limit. By default it greedily uses up all memory that is available. This
        /// is generally not required unless additional memory is required for other applications -
        /// or the system memory is very limited e.g. <16GB by default tool is configured to try to
        /// spill to disk, to prevent crashes.
        #[arg(long, default_value = None)]
        memory_limit_gb: Option<usize>,

        /// number of worker threads to limit async jobs to, by default uses up all available cpu threads.
        /// its advisable not to change this, unless you require reserved threads for other applications in
        /// some sort of shared setting.
        #[arg(long, default_value = None)]
        worker_threads: Option<usize>,

        /// Force this app to use the input data as a filesystem. I.e. input_path will point to a filesystem instead.
        #[arg(short, long, default_value_t = false)]
        force_filesystem: bool,
    },

    /// Attempts to infer the schema from the tar+pq object store. start_date/end_date specifies a
    /// date range of files to attempt to coerce into a schema. Otherwise, uses the schema from the
    /// first entry in the tar store.
    ///
    /// The main use case of this is if schemas between files don't match exactly and need to be  
    /// coerced. the output of this is a json format that can be fed into the `resample` command.
    ///
    /// Note:
    /// * Currently only supports parquet format as input, and json as output.
    /// * Similar to resample you can force the tool to get data from a raw parquet file instead of
    ///   a tar archive by using the force-fileystem flag. In this case, input_path will be a single
    ///   parquet file instead.
    InferSchema {
        /// tar file (object store) containing multiple .pq
        input_path: String,
        /// file path to store output schema, this will be in json format
        output_path: String,
        /// optional prefix (if it exists in file name) to retrieve the schema from. Note: this will retrieve from the first match
        #[arg(long, default_value = None)]
        prefix: Option<String>,

        /// Force this app to use the input data as a filesystem. I.e. input_path will point to a parquet file instead
        #[arg(short, long, default_value_t = false)]
        force_filesystem: bool,
    },
}
