#!/bin/bash

# Extracts parquet data from a compressed tar archive to a uncompressed tar archive without using up
# inode quota.
#
# Currently the tar'd parquet resampler tool does not support compression. In fact compression will
# probably remove any gains achieved from the archive so it's probably better to pre-extract data
# anyway. Currently, this script does that - but can be extended to the tool itself, to pre-extract
# the tarball in either a scratch space or 
#

# --- CHANGE THESE ---
COMPRESSED_ARCHIVE_PATH='nowboost.tar.gz'
PARQUET_PREFIX='./nowboost/tjl/one_minute_data/*.pq'
OUTPUT_ARCHIVE_PATH='one_min_testing.tar'

# IMPORTANT: files will be temporarily be generated in the current working directory as they are
# repackaged into a tar archive, please make sure the current directory does not contain anything
# that may be overwritten
# ---

tar -xzf $COMPRESSED_ARCHIVE_PATH  $PARQUET_PREFIX
        --to-command='mkdir -p $(dirname $TAR_FILENAME) && cat - > $TAR_FILENAME && tar f '$OUTPUT_ARCHIVE_PATH' $TAR_FILENAME --append --remove-files'
