from datetime import datetime, timedelta
from metloom.pointdata import SnotelPointData
import pandas as pd
import geopandas as gpd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from metpy.units import units
import metpy.calc as mpcalc
import math
import scipy
import os
import shutil
from pytz import UTC

sntls = pd.read_csv('/home/cdalden/summa_setup/analysis/sntl_list_ski_temps.csv')

# Initialize the 'mean_temp_djf' column with NaN values if it doesn't exist
if 'mean_temp_djf' not in sntls.columns:
    sntls['mean_temp_djf'] = np.nan

start_date = datetime(2000, 10, 1)
end_date = datetime(2024, 9, 30)

# Loop through the 'site' column and assign the corresponding 'state'
for index, row in sntls.iterrows():
    site = row['site_code']
    state = row['state']
    # %%
    # Pull desired variables from snotel to dataframe
    # snotel_point = SnotelPointData(snotel, "MyStation")
    snotel_point = SnotelPointData(f'{str(site)}:{str(state)}:SNTL', "MyStation")
    df = snotel_point.get_hourly_data(
        start_date, end_date,
        [snotel_point.ALLOWED_VARIABLES.TEMP]
    )

    # Specify latitude, longitude, and elevation from station metadata
    lat = snotel_point.metadata.y
    lon = snotel_point.metadata.x
    elev = snotel_point.metadata.z

    # Clean up the dataframe
    df.reset_index(inplace=True)

    # Rename columns
    replace = {'AIR TEMP':'airtemp', 'datetime':'time'}
    df.rename(columns=replace, inplace=True)
    df.set_index('time', inplace=True)

    # Select data for December, January, and February
    winter_months = df[(df.index.month == 12) | (df.index.month == 1) | (df.index.month == 2)] 
    mean_temp_djf = winter_months['airtemp'].mean()

    # Save the mean temperature for the winter months
    sntls.loc[sntls.site_code == site, 'mean_temp_djf'] = mean_temp_djf
    print(f'{site} mean winter temp: {mean_temp_djf}')
    print(sntls)

sntls['mean_temp_djf'] = (sntls['mean_temp_djf'] - 32) * 5.0/9.0

# Convert airtemp to Kelvin
sntls['mean_temp_djf'] = (1.03*(sntls['mean_temp_djf']-0.9)) # Currier snotel temp correction

sntls.to_csv('/home/cdalden/summa_setup/analysis/sntl_list_ski_temps.csv', index=False)