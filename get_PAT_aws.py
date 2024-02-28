import argparse
import requests
import boto3
import json

def get_secret(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

def refresh_access_token(client_id, client_secret, refresh_token):
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    response = requests.post(url, data=data, auth=(client_id, client_secret))
    return response.json()  # Contains the new access token

def main():
    parser = argparse.ArgumentParser(description='Refresh Dropbox access token.')
    parser.add_argument('--secret_name', required=True, help='The name of the AWS secret.')
    parser.add_argument('--region_name', required=True, help='The AWS region of the secret.')
    args = parser.parse_args()

    secrets = get_secret(args.secret_name, args.region_name)
    new_tokens = refresh_access_token(secrets['client_id'], secrets['client_secret'], secrets['refresh_token'])
    access_token = new_tokens['access_token']
    print(access_token)  # Print the access token to stdout

if __name__ == "__main__":
    main()