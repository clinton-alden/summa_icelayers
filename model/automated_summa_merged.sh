#!/bin/bash

# Read the CSV file line by line, skipping the first line
tail -n +2 /home/cdalden/summa_setup/analysis/sntl_list_ski_temps.csv | while IFS=, read -r _ _ state site_name _ _ _ _ _ _ _ site_code _ _
do
    # Define your sets of inputs
    site_codes=($(for i in $(seq 2000 2024); do echo "$site_code:$state"; done))
    echo "code = $site_codes"
    water_years=($(seq 2000 2024))
    site="$site_name"
    echo $site

# Define your sets of inputs
# site_codes=($(for i in $(seq 2000 2024); do echo "791:WA"; done))
# water_years=($(seq 2000 2024))
# site="stevenspass"

    # loop through warming scenarios
    declare -a temp_runs=("current" "+2K" "+4K")

    for run in "${temp_runs[@]}"; do
        output_names=($(for i in $(seq 2000 2024); do echo "${site}_${run}_WY${i:2:2}"; done))

        # Get the length of the arrays
        length=${#site_codes[@]}

        # Loop over the arrays
        for ((i=0; i<$length; i++)); do
        # Get the inputs for this iteration
        input1=${site_codes[$i]}
        input2=${water_years[$i]}
        input3=${output_names[$i]}

        # Provide input to the first Python script
        echo -e "$input1\n$input2\n$input3" | python3 snotel_to_pysumma_${run}.py

        echo "forcing file created, now running summa"

        # Replace the content of the text file with input3
        echo "'$input3.nc'" > forcings/forcing_file_list.txt

        # Run the second Python script
        python3 run_summa_stats.py

        echo "summa run for $input3 complete, check output folder for output file"

        done
    done

    # remove all output files for this site after stats are calculated
    rm ../model/output/output_${site}*
    rm /home/cdalden/summa_setup/model/forcings/${site}*
    
done