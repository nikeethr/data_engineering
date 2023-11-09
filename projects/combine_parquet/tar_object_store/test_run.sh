#!/bin/bash

export RUST_LOG='debug'

# ./target/release/tarpq_res resample \
#   --output-freq=one-hour \
#   --agg-fields="AIR_TEMP,DWPT" \
#   --output-format=parquet \
#   --memory-limit-gb=6 \
#   --worker-threads=4 \
#   --schema-ref-path='test.json' \
#   --partition-col='datafusion-default' \
#   '../combpq/blah2020.tar' \
#   '/home/nvr90/test_pydf/parquet/' \
#   'nowboost/tjl/one_minute_data'


export RUST_LOG='debug'

# to resample again from file system
# NOTE: the tool moves columns to lower case, as it is harder to handle otherwise
./target/release/tarpq_res resample \
  --output-freq=one-day \
  --agg-fields="air_temp,dwpt" \
  --station-field="stn_num" \
  --time-field="time_rsmpl" \
  --output-format=csv \
  --memory-limit-gb=6 \
  --worker-threads=4 \
  --partition-col='datafusion-default' \
  --force-filesystem \
  'file:///home/nvr90/test_pydf/parquet/' \
  '/home/nvr90/test_pydf/csv/' \
  '/'
