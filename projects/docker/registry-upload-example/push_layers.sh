#!/bin/bash


for i in *; do
    if [[ "$i" =~ sha256__* ]]; then
        # Get location of blob URL
        echo "====> Get Blob upload location"
        url=$(
            curl -X POST "localhost:5000/v2/awra-base/blobs/uploads/" -v --silent 2>&1 \
            | grep Location \
            | sed 's/.*Location: //'
        )
        location=${url%$'\r'}
        echo "====> Uploading blob ${i} to location: ${location}"
        i_strip=${i#sha256__}
        curl -vX PUT "${location}&digest=sha256:${i_strip}" \
            --data-binary @$i \
            --header "Content-Type: application/octet-stream"
    fi
done

