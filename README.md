# oikobrowser_dropbox_autointegrate
Scripts needed for the automatic integration of files on dropbox to JSON config file for jbrowse2

## Files

### poll_dropbox.py
This script is untested.
Check dropbox every 10 seconds and runs bash script with a delay of 2 mins after final change.

usage:
```shell
python poll_dropbox.py --secret_name "oikobrowser_pull_token" --region_name "ap-southeast-2" --folder_path "/annotathon 2024/resources" --bash_script_path "create_json_all '/annotathon 2024/resources'"

```

### create_json_all
This is the bash script that runs the python scripts

### create_json.py
Main python file to generate JSON files for bigwig and gtf files

### dockerfile
Dockerfile needed to create the docker container containing the scripts

### get_PAT_aws.py
This script is untested, gets PAT from aws secrets manager

usage:
```shell
python get_access_token.py --secret_name "oikobrowser_pull_token" --region_name "ap-southeast-2"
```
