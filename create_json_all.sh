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

jbrowse add-assembly "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/O10v1/O10_primary_assembly.fa" -a "O10" -n "O10" -t indexedFasta \
    --faiLocation "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/O10v1/O10_primary_assembly.fa.fai" --displayName "Oikopleura dioica Osaka (O10)"




# generate json files
python "$original_cwd/create_json.py" -o "$target_jbrowse/individual_json" --input_dir "$folder_path" --access_token "$access_token" --target_jbrowse "$target_jbrowse"


# Iterate over each .json file in the directory
for file in $target_jbrowse/individual_json/*.json; do
  # Execute the jbrowse command for each file
  jbrowse add-track-json "$file" -u
done

# index text everytime this script is run
jbrowse text-index --attributes="Name,ID,gene_name" --force
