#!/bin/sh

# Correct way to get the script's directory is using $1, which is the first argument
target_jbrowse=$1
folder_path=$2
access_token=$3

# Capture the current working directory
original_cwd=$(pwd)

# Navigate to the jbrowse2 directory
cd "$target_jbrowse" || exit

# add assembly manually
jbrowse add-assembly "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/Bar2_p4/Bar2_p4.fa" -a "Bar2_p4" -n "Bar2_p4" -t indexedFasta \
    --faiLocation "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/Bar2_p4/Bar2_p4.fa.fai" --displayName "Oikopleura dioica Barcelona (Bar2_p4)"

jbrowse add-assembly "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OKI.I69/OKI.I69.fa" -a "OKI.I69" -n "OKI.I69" -t indexedFasta \
    --faiLocation "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OKI.I69/OKI.I69.fa.fai" --displayName "Oikopleura dioica Okinawa (OKI2018_I69)"

jbrowse add-assembly "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OSKA2016v1.9/OSKA2016v1.9.fa" -a "OSKA2016v1.9" -n "OSKA2016v1.9" -t indexedFasta \
    --faiLocation "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OSKA2016v1.9/OSKA2016v1.9.fa.fai" --displayName "Oikopleura dioica Osaka (OSKA2016v1.9)"

jbrowse add-assembly "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OdB3/Oidioi_genome.fasta" -a "OdB3" -n "OdB3" -t indexedFasta \
    --faiLocation "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OdB3/Oidioi_genome.fasta.fai" --displayName "Oikopleura dioica Norway (OdB3)"

# generate json files
python "$original_cwd/create_json.py" -o ~/temp --input_dir "$folder_path" --access_token "$access_token"


# Iterate over each .json file in the directory
for file in ~/temp/*.json; do
  # Execute the jbrowse command for each file
  jbrowse add-track-json "$file" -u
done

rm -r ~/temp

# index text everytime this script is run
jbrowse text-index --attributes="Name,ID,gene_name" --force