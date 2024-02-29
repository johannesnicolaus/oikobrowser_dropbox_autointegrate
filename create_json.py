#!/home/n/nicolaus-johannes/miniconda3/bin/python3

import dropbox
from dropbox.exceptions import ApiError
import json
import os
import argparse

# Argument parsing
parser = argparse.ArgumentParser(description="Generate JBrowse JSON configs from Dropbox files.")
parser.add_argument("-o", "--output_dir", required=True, help="Directory to store JSON files")
parser.add_argument("-a", "--access_token", required=True, help="Dropbox access token")
parser.add_argument("-i", "--input_dir", required=True, help="Dropbox folder path to process")

args = parser.parse_args()

# Initialize a Dropbox object
dbx = dropbox.Dropbox(args.access_token)

def list_files_recursively(dbx, path):
    try:
        result = dbx.files_list_folder(path, recursive=True)
    except dropbox.exceptions.ApiError as err:
        print(f"Folder listing failed for {path}: {err}")
        return []
    files = []
    for entry in result.entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            files.append(entry)
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                files.append(entry)
    return files
    
def create_or_get_shared_link(dbx, file_entry):
    try:
        link_metadata = dbx.sharing_create_shared_link_with_settings(file_entry.path_display)
        return link_metadata.url
    except ApiError as error:
        if 'shared_link_already_exists' in str(error):
            links = dbx.sharing_list_shared_links(path=file_entry.path_display, direct_only=True).links
            return links[0].url if links else "No link found"
        else:
            print(f"Error creating or getting shared link for {file_entry.path_display}: {error}")
            return "Error"

def determine_track_type(file_name):
    if file_name.lower().endswith(".bigwig"):
        return "BigWigAdapter"
    elif file_name.lower().endswith(".bed"):
        return "BedAdapter"
    elif file_name.lower().endswith(".gff3"):
        return "Gff3Adapter"
    elif file_name.lower().endswith(".gff"):
        return "Gff3Adapter"
    elif file_name.lower().endswith(".gtf"):
        return "GtfAdapter"
    else:
        return None

def generate_jbrowse_json_config(file_entry, direct_link):
    parts = file_entry.path_display.lstrip("/").split("/")
    if len(parts) >= 4:
        assemblyNames = parts[-3]
        category_path = parts[-2]
        file_name = parts[-1]
        trackType = determine_track_type(file_name)
        
        if trackType:
            trackID = f"{assemblyNames}_{category_path.replace('/', '_')}_{file_name.replace(' ', '_')}"
            categories = category_path.split('/')
            
            config = {
                "trackId": trackID,
                "name": file_name,
                "assemblyNames": [assemblyNames],
                "category": categories,
                "adapter": {
                    "type": trackType,
                }
            }
            
            if trackType == "BigWigAdapter":
                config["type"] = "QuantitativeTrack"
                config["adapter"]["bigWigLocation"] = {
                    "locationType": "UriLocation",
                    "uri": direct_link
                }
            elif trackType in ["Gff3Adapter", "BedAdapter", "GtfAdapter"]:
                config["type"] = "FeatureTrack"
                locationKey = "gtfLocation" if trackType == "GtfAdapter" else "bedLocation" if trackType == "BedAdapter" else "gffLocation"
                config["adapter"][locationKey] = {
                    "locationType": "UriLocation",
                    "uri": direct_link
                }
                # Add transcriptType for Gff3Adapter
                if trackType in ["Gff3Adapter", "GtfAdapter"]:
                    config["adapter"]["transcriptType"] = "transcript"
                    
            return trackID, config
    return None, None

# Create the output directory if it does not exist
os.makedirs(args.output_dir, exist_ok=True)

# List all files in the folder and its subfolders
files = list_files_recursively(dbx, args.input_dir)

# Example loop through your files
for file in files:
    shared_link = create_or_get_shared_link(dbx, file)
    direct_link = shared_link.replace("www.dropbox.com", "dl.dropboxusercontent.com").replace("?dl=0", "")
    trackID, config = generate_jbrowse_json_config(file, direct_link)
    if config:
        # Construct the file path
        file_path = os.path.join(args.output_dir, f"{trackID}.json")

        # Print message indicating that a JSON file is being generated
        print(f"Generating JSON for file: {file.name}")

        # Write the JSON configuration to the file
        with open(file_path, 'w') as json_file:
            json.dump(config, json_file, indent=2)

print("finished writing json files")