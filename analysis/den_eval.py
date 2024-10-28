import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import xarray as xr
import sys

year_suffix = sys.argv[1]
run_name = 'harts_current_WY'+str(year_suffix)
summa = xr.open_dataset('../model/output/harts_pass/output_'+run_name+'_timestep.nc')

snotel = pd.read_csv('../model/snotel_csvs/harts_current_WY'+str(year_suffix)+'.csv', index_col='time', parse_dates=True)

# mask out bad snow depth data
snotel['SNOWDEPTH'] = snotel['SNOWDEPTH'][snotel['SNOWDEPTH'] > 0]
# Calculate the difference between timesteps
diff = snotel['SNOWDEPTH'].diff()
# Mask out all data where the difference between timesteps is more than 0.5
snotel['SNOWDEPTH'] = snotel['SNOWDEPTH'][diff.abs() <= 6]
snotel['SNOWDEPTH'] = snotel['SNOWDEPTH'].interpolate(method='linear')

# mask out bad SWE data
snotel['SWE'] = snotel['SWE'][snotel['SWE'] > 0]
snotel['SWE'] = snotel['SWE'].interpolate(method='linear')

# calculate density
summa['density'] = (summa['scalarSWE'])/summa['scalarSnowDepth']
snotel['density_obs'] = (snotel['SWE']*25.4)/(snotel['SNOWDEPTH']*0.0254)

# Convert 'density' DataArray in 'summa' to DataFrame
density_df = summa['density'].to_dataframe()
# Reset the index
density_df = density_df.reset_index()
# Set 'time' as the index
density_df = density_df.set_index('time')
# Drop the 'hru' column
density_df = density_df.drop(columns='hru')

# Round the DateTimeIndex of 'density_df' to the nearest hour
density_df.index = density_df.index.round('H')

# Round the DateTimeIndex of 'snotel' to the nearest hour
snotel.index = snotel.index.round('H')

# Make the DateTimeIndex of 'density_df' timezone-naive
density_df.index = density_df.index.tz_localize(None)

# Make the DateTimeIndex of 'snotel' timezone-naive
snotel.index = snotel.index.tz_localize(None)

# Subtract 'density' in 'snotel' from 'density' in 'density_df'
difference = density_df['density'] - snotel['density_obs']

# Subtract 'density' in 'snotel' from 'density' in 'density_df'
difference = density_df['density'] - snotel['density_obs']

# Drop NaN values
difference = difference.dropna()

# Mask out all data that is not between December and March
masked_difference = difference[(difference.index.month >= 12) | (difference.index.month <= 3)]

mean_den_dif = masked_difference.mean()

df = pd.read_csv('den_eval.csv', index_col=0)

# Find the row with index='year_suffix' and assign 'mean_den_dif'
df.loc[str(year_suffix), 'mean_den_dif'] = mean_den_dif

# Append the DataFrame to the CSV file (and create it if it doesn't exist)
df.to_csv('den_eval.csv')