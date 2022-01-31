#!/bin/bash

echo "-- reset db --"
python3 installation/init_db.py

echo "-- reset images --"
rm -rf uploads
mkdir ./uploads
cp -r installation/uploads_backup/. uploads