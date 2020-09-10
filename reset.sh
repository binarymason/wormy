#!/usr/bin/env bash

rm -rf data
mkdir -p data/images
touch data/.gitkeep
echo '{ "idx": 0 }' > data/meta.json
