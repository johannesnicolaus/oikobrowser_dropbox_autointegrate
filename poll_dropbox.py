import argparse
import requests
import boto3
import json
import subprocess
import time
import dropbox

# Function to get the secret from AWS Secrets Manager
def get_secret(secret_name, region_name):
    print("Getting secret from AWS Secrets Manager...")
    try:
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=region_name)
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret = get_secret_value_response['SecretString']
        print("Secret retrieved successfully.")
        return json.loads(secret)
    except Exception as e:
        print(f"Failed to retrieve secret: {e}")
        raise

# Function to refresh the Dropbox access token
def refresh_access_token(client_id, client_secret, refresh_token):
    print("Refreshing access token...")
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    try:
        response = requests.post(url, data=data, auth=(client_id, client_secret))
        response_data = response.json()
        if 'access_token' not in response_data:
            print(f"Failed to refresh access token: {response_data}")
            raise Exception(f"Failed to refresh access token: {response_data}")
        print("Access token refreshed successfully.")
        return response_data
    except Exception as e:
        print(f"Error refreshing access token: {e}")
        raise

# Main function to poll Dropbox for changes
def poll_dropbox_changes(secret_name, region_name, folder_path, bash_script_path, target_jbrowse):
    # Retrieve the initial Dropbox credentials and access token
    secrets = get_secret(secret_name, region_name)
    access_token = refresh_access_token(secrets['client_id'], secrets['client_secret'], secrets['refresh_token'])['access_token']
    
    # Initialize the Dropbox client with the access token
    dbx = dropbox.Dropbox(access_token)
    print("Dropbox client initialized.")
    response = dbx.files_list_folder(folder_path, recursive=True)
    cursor = response.cursor
    print(f"Initial list_folder successful, cursor: {cursor}")
    change_detected_time = None

    while True:
        print("Polling for changes...")
        # Refresh the access token every hour to ensure the script continues to have access
        current_time = time.time()
        if not 'last_refresh_time' in globals() or current_time - last_refresh_time >= 3600:
            print("Refreshing access token...")
            access_token = refresh_access_token(secrets['client_id'], secrets['client_secret'], secrets['refresh_token'])['access_token']
            dbx = dropbox.Dropbox(access_token)
            globals()['last_refresh_time'] = current_time
        
        try:
            # Check for any changes in the Dropbox folder
            response = dbx.files_list_folder_continue(cursor)
            if response.entries:  # If there are changes detected
                print("Changes detected.")
                change_detected_time = time.time()
            cursor = response.cursor
        except dropbox.exceptions.ApiError as err:
            # Handle any API errors, such as token expiration
            print("API error:", err)
            time.sleep(60)  # Wait a minute before trying again
            continue

        # Execute the bash script if 2 minutes have passed since the last detected change
        if change_detected_time and (time.time() - change_detected_time >= 120):
            print("2 minutes passed since last change, executing bash script...")
            subprocess.call(['bash', bash_script_path, target_jbrowse, args.folder_path, access_token])
            change_detected_time = None  # Reset the timer
        
        time.sleep(300)  # Check for changes every 5 mins
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitor Dropbox folder for changes and execute a bash script on change.')
    parser.add_argument('--secret_name', required=True, help='The name of the AWS secret containing Dropbox credentials.')
    parser.add_argument('--region_name', required=True, help='The AWS region of the secret.')
    parser.add_argument('--folder_path', required=True, help='The Dropbox folder path to monitor for changes.')
    parser.add_argument('--bash_script_path', required=True, help='The path to the bash script to execute on change.')
    parser.add_argument('--target_jbrowse', required=True, help='The target JBrowse directory to use in the bash script.')
    args = parser.parse_args()

    poll_dropbox_changes(args.secret_name, args.region_name, args.folder_path, args.bash_script_path, args.target_jbrowse)
