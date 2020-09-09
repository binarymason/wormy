#!/usr/bin/env bash

mkdir -p data/images
rm -rf data/images/*.png
rm -rf data/labels.csv
echo '{ "idx": 0 }' > data/meta.json
