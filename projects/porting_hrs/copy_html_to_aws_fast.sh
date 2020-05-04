#!/bin/sh


web_dir=/c/Users/Nikeeth/Documents/wfs/hrs/review-2020/data_B/web_output
s3_bucket=s3://review-hrs-bucket

cd $web_dir

aws s3 cp $web_dir $s3_bucket --content-type="text/html" --exclude="*" --include="*.table" --recursive
