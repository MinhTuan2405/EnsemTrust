#!/bin/bash

if [ -z "$1" ]; then
    NOW=$(date +"%Y-%m-%d %H:%M:%S")
    MSG="sync at $NOW"
else
    MSG="$1"
fi

echo "Commit message: $MSG"

git add .
git commit -m "$MSG"
git push
