#!/bin/bash

# restore original credentials with confirmation
mv ~/.aws/credentials.bak ~/.aws/credentials \
    --interactive
