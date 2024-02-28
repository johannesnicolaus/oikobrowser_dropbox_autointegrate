import argparse
import requests
import boto3
import json
import subprocess
import time
import dropbox

# Function to get the secret from AWS Secrets Manager
def get_secret(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

# Function to refresh the Dropbox access token
def refresh_access_token(client_id, client_secret, refresh_token):
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = requests.post(url, data=data, auth=(client_id, client_secret))
    return response.json()  # Contains the new access token

# Main function to poll Dropbox for changes
def poll_dropbox_changes(secret_name, region_name, folder_path, bash_script_path):
    secrets = get_secret(secret_name, region_name)
    access_token = refresh_access_token(secrets['client_id'], secrets['client_secret'], secrets['refresh_token'])['access_token']
    
    dbx = dropbox.Dropbox(access_token)
    response = dbx.files_list_folder(folder_path, recursive=True)
    cursor = response.cursor
    change_detected_time = None

    while True:
        # Refresh the access token every hour
        current_time = time.time()
        if not 'last_refresh_time' in globals() or current_time - last_refresh_time >= 3600:
            access_token = refresh_access_token(secrets['client_id'], secrets['client_secret'], secrets['refresh_token'])['access_token']
            dbx = dropbox.Dropbox(access_token)
            globals()['last_refresh_time'] = current_time
        
        try:
            response = dbx.files_list_folder_continue(cursor)
            if response.entries:  # If there are changes
                print("Changes detected.")
                change_detected_time = time.time()
            cursor = response.cursor
        except dropbox.exceptions.ApiError as err:
            # Handle expiration or other API errors
            print("API error:", err)
            time.sleep(60)  # Wait a minute before trying again
            continue

        # Check if 2 minutes have passed since the last detected change
        if change_detected_time and (time.time() - change_detected_time >= 120):
            print("2 minutes passed since last change, executing bash script...")
            subprocess.call(['bash', bash_script_path])
            change_detected_time = None  # Reset the timer
        
        time.sleep(10)  # Check for changes every 10 seconds

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitor Dropbox folder for changes and execute a bash script on change.')
    parser.add_argument('--secret_name', required=True, help='The name of the AWS secret containing Dropbox credentials.')
    parser.add_argument('--region_name', required=True, help='The AWS region of the secret.')
    parser.add_argument('--folder_path', required=True, help='The Dropbox folder path to monitor for changes.')
    parser.add_argument('--bash_script_path', required=True, help='The path to the bash script to execute on change.')
    args = parser.parse_args()

    poll_dropbox_changes(args.secret_name, args.region_name, args.folder_path, args.bash_script_path)
