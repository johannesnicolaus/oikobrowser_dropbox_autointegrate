#!/bin/python

import dropbox
from dropbox.exceptions import ApiError
import json
import os
import argparse
import subprocess

# Argument parsing
parser = argparse.ArgumentParser(description="Generate JBrowse JSON configs from Dropbox files.")
parser.add_argument("-o", "--output_dir", required=True, help="Directory to store JSON files")
parser.add_argument("-a", "--access_token", required=True, help="Dropbox access token")
parser.add_argument("-i", "--input_dir", required=True, help="Dropbox folder path to process")
parser.add_argument("-j", "--target_jbrowse", required=True, help="Target jbrowse directory")

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
    elif file_name.lower().endswith(".chain"):
        return "ChainAdapter"
    else:
        return None

def generate_jbrowse_json_config(file_entry, direct_link):
    parts = file_entry.path_display.lstrip("/").split("/")
    if len(parts) >= 4:
        assemblyNames = parts[-3]
        category_path = parts[-2]
        file_name = parts[-1]
        file_name_without_extension, extension = os.path.splitext(file_name)
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
            elif trackType == "ChainAdapter":
                query_assembly = file_name_without_extension  # For .chain files, the query assembly is derived from the file name
                # Assume the target assembly needs to be determined or set here. For demonstration, using 'assemblyNames' as placeholder
                target_assembly = assemblyNames  # This might need adjustment based on how you determine the target assembly
                
                # Unique trackID for .chain files, consider including more unique attributes if necessary
                trackID = f"{query_assembly}_{target_assembly}"

                # Constructing the configuration for a chain file
                config = {
                    "type": "SyntenyTrack",
                    "trackId": trackID,
                    "name": file_name,  # or adjust as needed
                    "assemblyNames": [target_assembly, query_assembly],  # The order depends on your specific requirement
                    "adapter": {
                        "type": "ChainAdapter",
                        "targetAssembly": target_assembly,
                        "queryAssembly": query_assembly,
                        "chainLocation": {
                            "locationType": "UriLocation",
                            "uri": direct_link  # Direct link to the chain file
                        }
                    },
                    "displays": [
                        {"type": "DotplotDisplay", "displayId": f"{trackID}-DotplotDisplay"},
                        {"type": "LinearComparativeDisplay", "displayId": f"{trackID}-LinearComparativeDisplay"},
                        {"type": "LinearSyntenyDisplay", "displayId": f"{trackID}-LinearSyntenyDisplay"},
                        {"type": "LGVSyntenyDisplay", "displayId": f"{trackID}-LGVSyntenyDisplay"}
                    ]
                }   
            return trackID, config
    return None, None

# Initialize the list to track generated or verified track IDs
generated_track_ids = []

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
        generated_track_ids.append(trackID)
        file_path = os.path.join(args.output_dir, f"{trackID}.json")
        # Only generate JSON if it doesn't already exist
        if not os.path.exists(file_path):
            print(f"Generating JSON for file: {file.name}")
            with open(file_path, 'w') as json_file:
                json.dump(config, json_file, indent=2)

# this function is untested, it's possible that jbrowse remove-track {json_file} works better (using json file instead of track id)
def get_existing_track_ids_from_config(config_path):
    """
    Extract 'trackId' values from the config.json by searching lines that contain 'trackId'.
    """
    existing_track_ids = []
    try:
        with open(config_path, 'r') as file:
            for line in file:
                if '"trackId":' in line:
                    # Extract the trackId value from the line
                    parts = line.split('"trackId": "')
                    if len(parts) > 1:
                        track_id = parts[1].split('"')[0]  # Get the string between the quotes
                        existing_track_ids.append(track_id)
    except Exception as e:
        print(f"Error reading config.json: {e}")
    
    return existing_track_ids

# this can be used but still broken to remove tracks if they are not in the json file list
# def clean_up_old_tracks(target_jbrowse, output_dir, generated_track_ids):
#     config_path = os.path.join(target_jbrowse, "config.json")
    
#     print(f"Looking for config.json at: {config_path}")
    
#     existing_track_ids = get_existing_track_ids_from_config(config_path)
    
#     print("Existing track IDs in config:", existing_track_ids)
    
#     tracks_to_remove = [track_id for track_id in existing_track_ids if track_id not in generated_track_ids]
    
#     print("Tracks to remove:", tracks_to_remove)

#     for track_id in tracks_to_remove:
#         print(f"Removing track for deleted file: '{track_id}'")
#         jbrowse_command = f'jbrowse remove-track "{track_id}" --out "{target_jbrowse}"'
#         print("Executing command:", jbrowse_command)
#         subprocess.run(jbrowse_command, shell=True, capture_output=True, text=True)
        
#         # Attempt to remove any corresponding JSON files in output_dir
#         json_file = f"{track_id}.json"
#         json_file_path = os.path.join(output_dir, json_file)
#         if os.path.exists(json_file_path):
#             print(f"Removing JSON file for deleted track: {json_file}")
#             os.remove(json_file_path)

def clean_up_old_tracks(output_dir, generated_track_ids, target_jbrowse):
    """
    Remove tracks from JBrowse configuration for tracks not present in Dropbox.
    """
    existing_json_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    for json_file in existing_json_files:
        json_file_path = os.path.join(output_dir, json_file)
        with open(json_file_path, 'r') as f:
            config = json.load(f)
            track_id = config.get('trackId', '')

        # If the track ID from the file is not in the list of generated/verified track IDs, remove it
        if track_id and track_id not in generated_track_ids:
            print(f"Removing track for deleted file: {track_id}")
            # Use subprocess to call jbrowse remove-track with the track ID
            jbrowse_command = f'jbrowse remove-track "{track_id}" --out "{target_jbrowse}"'
            print("Executing command:", jbrowse_command)
            # Execute the command
            subprocess.run(jbrowse_command, shell=True, capture_output=True, text=True)

            # Remove the JSON file as it's no longer needed
            os.remove(json_file_path)

# Clean up JSON files and tracks for deleted Dropbox files
clean_up_old_tracks(args.output_dir, generated_track_ids, args.target_jbrowse)


print("finished writing json files")