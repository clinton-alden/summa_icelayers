#!/bin/bash

# Directory containing the .nc files
dir="../model/output/harts_pass/"

# Loop through all .nc files in the directory
for file in "$dir"/*.nc; do
    # Extract the filename without the path and extension
    filename=$(basename "$file" .nc)

    # Split the filename at the underscores
    IFS='_' read -ra parts <<< "$filename"

    # Extract the required parts and format the input string
    input="${parts[1]}_${parts[2]}_${parts[3]}"
    echo $input

    # Execute the Python script with the input string
    echo "$input" | python /home/cdalden/summa_setup/analysis/crust_stats.py 
done