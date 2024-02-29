#!/bin/sh

# get the jbrowse2 directory from argument
cd $0

# add assembly manually
jbrowse add-assembly "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/Bar2_p4/Bar2_p4.fa" -a "Bar2_p4" -n "Bar2_p4" -t indexedFasta \
    --faiLocation "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/Bar2_p4/Bar2_p4.fa.fai" --displayName "Oikopleura dioica Barcelona (Bar2_p4)"

jbrowse add-assembly "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OKI.I69/OKI.I69.fa" -a "OKI.I69" -n "OKI.I69" -t indexedFasta \
    --faiLocation "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OKI.I69/OKI.I69.fa.fai" --displayName "Oikopleura dioica Okinawa (OKI2018_I69)"

jbrowse add-assembly "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OSKA2016v1.9/OSKA2016v1.9.fa" -a "OSKA2016v1.9" -n "OSKA2016v1.9" -t indexedFasta \
    --faiLocation "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OSKA2016v1.9/OSKA2016v1.9.fa.fai" --displayName "Oikopleura dioica Osaka (OSKA2016v1.9)"

jbrowse add-assembly "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OdB3/Oidioi_genome.fasta" -a "OdB3" -n "OdB3" -t indexedFasta \
    --faiLocation "https://raw.githubusercontent.com/oist//Oikopleuradioica_genomeannotation/main/OdB3/Oidioi_genome.fasta.fai" --displayName "Oikopleura dioica Norway (OdB3)"

# get access token using AWS Secrets Manager
# Example: --secret_name oikobrowser_pull_token --region_name ap-southeast-2
ACCESS_TOKEN=$(python get_access_token.py --secret_name "YOUR_SECRET_NAME" --region_name "YOUR_REGION_NAME")

# generate json files
create_json.py -o ~/temp -a $0 -i $1

# Iterate over each .json file in the directory
for file in ~/temp/*.json; do
  # Execute the jbrowse command for each file
  jbrowse add-track-json "$file" -u
done

rm -r ~/temp

# index text everytime this script is run
jbrowse text-index --attributes="Name,ID,gene_name" --force