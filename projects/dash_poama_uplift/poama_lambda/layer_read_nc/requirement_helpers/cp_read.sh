#!/bin/sh

READ_DIRS=read_files.txt

while IFS= read -r line
do
  cp -r --parents "$line" read_paths/
done < "$READ_DIRS"
