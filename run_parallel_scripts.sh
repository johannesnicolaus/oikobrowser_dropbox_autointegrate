#!/bin/bash

# Start the first Python script in the background
python poll_dropbox.py --secret_name oikobrowser --region_name ap-northeast-1 --folder_path "/oikobrowser/public" --bash_script_path ./create_json_all.sh --target_jbrowse /var/www/html/jbrowse-public &

# Start the second Python script in the background
python poll_dropbox.py --secret_name oikobrowser --region_name ap-northeast-1 --folder_path "/oikobrowser/private" --bash_script_path ./create_json_all.sh --target_jbrowse /var/www/html/jbrowse-private &

# Wait for both jobs to finish
wait