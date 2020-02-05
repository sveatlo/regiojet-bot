#!/usr/bin/bash

FROM=$1
TO=$2
DATE=$3

if [[ -d ./venv ]]; then
    source venv/bin/activate
fi
source .env

python main.py --from "$FROM" --to "$TO" --date "$DATE"
