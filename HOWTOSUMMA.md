This repository (summa_icelayers/model) includes the code needed to run the Structure for 
Unifying Multiple Modeling Alternatives model (Clark et al. 2015a, 2015b, 2015c). 

How to run SUMMA for a SNOTEL:

## STEP 1
To start, try to create an environment from the pysumma.yml file in the summa_icelayers 
repository. If this does not work, you can try to install the pysumma python package using
pip or conda. The pysumma package that has worked previously uses python version 3.9.15.
The other necessary packages are metloom, metpy, and metsim. Installing these 4 with conda 
should install all other dependencies

This step has caused significant issues installing pysumma. One trick that has worked before
is deleting your install of conda/anaconda/miniconda/miniforge and reinstalling fresh. This 
comes with the warning that it will delete all of your other environments so proceed with 
caution.

## STEP 2
Once the environment is set up (pysumma, metloom, metsim, metpy), activate the environment
from the command line and navigate to the summa_icelayers/model directory. 

## STEP 3a
With the pysumma environment activated, run ./one_step_summa.sh 
You will be prompted to enter information 3 times. Enter it in the format given by the examples.

## STEP3b
Enter the numeric code for your SNOTEL followed by a colon and the state. 
For example, the code for Harts Pass, WA is 515 so you would enter '515:WA' and hit enter 
(without the quotes). You can find the codes and available snotels activate
https://www.nrcs.usda.gov/resources/data-and-reports/snow-and-water-interactive-map

Click on the site and then click on metadata to get the station ID.

## STEP3c
Enter the water year you want to simulate. The water year runs from October 1 to September 30.
If interested in simulating winter 2023/2024 you would type '2024' and hit enter (without the
quotes). This will run for October 1, 2023 to September 2024.

## STEP 3d
Enter the output file name. For Harts Pass for 2024, I recommend 'hartspass_WY24' and hit enter
(without the quotes).

## STEP 4
Wait 2-4 minutes for the simulation to complete. It will print 'Model status: success' if it was
successful. You can find your output .nc file in the model/output directory. 

## STEP 5
Fun analysis! The bottom of this file has plotting example code:
'summa_icelayers/analysis/06_mean_airtemp.ipynb'

Change the 'out' variable to reflect your output file and open the file with xarray. 
For a simple plot, try 'out.scalarSnowDepth.plot()' for the snowdepth plot.