#!/bin/bash

export RUST_LOG='debug'

./target/release/tarpq_res \
  --output-freq=ten-mins \
  --agg-fields="AIR_TEMP,DWPT" \
  --output-format=csv \
  --memory-limit-gb=6 \
  --worker-threads=4 \
  '../combpq/blah2020.tar' \
  './test' \
  'nowboost/tjl/one_minute_data'
