# %%
import xarray as xr
import os
import numpy as np
import pandas as pd
from datetime import datetime
import datetime
import matplotlib.pyplot as plt
import pysumma as ps
import pysumma.plotting as psp
import warnings

# pysumma has many depreciated packages, this ignores their warnings
warnings.filterwarnings("ignore", category=UserWarning)

# %%
executable = 'summa.exe'
filemanager = '/home/cdalden/summa_setup/model/settings/file_manager_summa.txt'

# Create a pySUMMA simulation object
s = ps.Simulation(executable, filemanager)


# Set the simulation start and end times from forcing file
with open('./forcings/forcing_file_list.txt', 'r') as file:
    # Read the contents
    forcing_file = file.read().replace("'", "")
forcing = xr.open_dataset('./forcings/'+forcing_file.strip(), engine='netcdf4')
time = forcing['time']

dt64 = np.datetime64(time.isel(time=0).values)
dt = pd.to_datetime(dt64)
start = dt.strftime('%Y-%m-%d %H:%M')
dt64 = np.datetime64(time.isel(time=-1).values)
dt = pd.to_datetime(dt64)
end = dt.strftime('%Y-%m-%d %H:%M')

s.manager['simStartTime'] = start
s.manager['simEndTime'] = end

# Add in some additional variables so we can demonstrate plotting capabilities
output_settings = {'period': 1, 'instant': 1, 'sum': 0, 
              'mean': 0, 'variance': 0, 'min': 0, 'max': 0}
layer_vars = ['mLayerTemp', 'mLayerDepth', 'mLayerHeight',
              'mLayerLiqFluxSoil', 'mLayerVolFracIce', 'mLayerVolFracLiq', 
              'mLayerVolFracWat','mLayerMatricHead', 'iLayerHeight', 'scalarSnowDepth', 'nSnow']

# Create the new variables
for var in layer_vars:
    s.output_control[var] = output_settings

# Ensure all variables have the same statistics
all_vars = set(layer_vars + [o.name for o in s.output_control.options])
for var in all_vars:
    s.output_control[var] = output_settings

# Set params
s.decisions['snowLayers'] = 'jrdn1991'
s.decisions['thCondSnow'] = 'tyen1965'
s.decisions['snowDenNew'] = 'hedAndPom'
s.decisions['compaction'] = 'consettl'
s.decisions['astability'] = 'mahrtexp'

s.global_hru_params['tempCritRain'] = 273.15
s.global_hru_params['newSnowDenMin'] = 50
s.global_hru_params['densScalGrowth'] = 0.10
s.global_hru_params['densScalOvrbdn'] = 0.025
s.global_hru_params['fixedThermalCond_snow'] = 0.35
s.global_hru_params['Fcapil'] = 0.04 # intially 0.06 for salmon
# s.global_hru_params['albedoDecayRate'] = 1.0d+5

out_name = os.path.splitext(forcing_file)[0]
# Run the model, specify the output suffix
# print('********** MODEL INITIALIZED **********')
# print('********** estimated runtime ~30 seconds **********')
s.run('local', run_suffix=out_name)

# %%
print('Model status:', s.status)


# Create and save density and temp profile plots
summa = s.output


def justify(a, invalid_val=np.nan, axis=1, side='right'):
    """
    Justifies a 2D array
    Courtesy: https://stackoverflow.com/questions/44558215/python-justifying-numpy-array/44559180#44559180

    Parameters
    ----------
    A : ndarray
        Input array to be justified
    axis : int
        Axis along which justification is to be made
    side : str
        Direction of justification. It could be 'left', 'right', 'up', 'down'
        It should be 'left' or 'right' for axis=1 and 'up' or 'down' for axis=0.

    """
    if invalid_val is np.nan:
        mask = ~np.isnan(a)
    else:
        mask = a!=invalid_val
    justified_mask = np.sort(mask,axis=axis)
    if (side=='up') | (side=='left'):
        justified_mask = np.flip(justified_mask,axis=axis)
    out = np.full(a.shape, invalid_val)
    if axis==1:
        out[justified_mask] = a[mask]
    else:
        out.T[justified_mask.T] = a.T[mask.T]
    return out


depth = summa.isel(hru=0)['iLayerHeight']
var = summa.isel(hru=0)['mLayerVolFracWat']
temp = summa.isel(hru=0)['mLayerTemp']
vmask = var != -9999
dmask = depth != -9999
tmask = temp != -9999
depth.values = justify(depth.where(dmask).values)
var.values = justify(var.where(vmask).values)
temp.values = justify(temp.where(tmask).values)

# Calculate the average at all layers
average = temp.mean(dim='midToto')

# Filter var where the average is less than 273.15
filtered_var = var.where(average < 273.05)

# filter for layers within top 1m
# max_depth = summa.isel(hru=0)['iLayerHeight'].max(dim='ifcToto') - 1
# filtered_var = filtered_var.where(summa.isel(hru=0)['iLayerHeight'] > max_depth)

# Calculate the vertical derivative
derivative = filtered_var.diff(dim='midToto')

# Initialize the list to store counts
counts = []

# Loop over the 'time' dimension within the specified range
for t in var.time.values[1464:4393]:
    # Select the derivative for the current timestep
    derivative_t = derivative.sel(time=t)

    # Calculate the running average over 3 layers
    running_avg = derivative_t.rolling(midToto=3, center=False).sum()

    # Filter values that are greater than or equal to 0.2 or less than or equal to -0.2
    threshold = 0.15
    filtered = running_avg.where((running_avg >= threshold) | (running_avg <= -threshold))

    # Count the number of layers with at least one such value
    count = np.isfinite(filtered).sum().values

    # Append the count to the list
    counts.append(count)

# Convert the list to a numpy array
counts = np.array(counts)

crust_days = counts.sum() / 24
mean_crusts = counts.mean()

# binary crust metric
crusts_binary = np.where(counts > 0, 1, 0).sum()

# Calculate '-summa['iLayerHeight'].isel(ifcToto=nSnow)'
nSnow = summa['nSnow'].values[0] # assuming 'nSnow' is a variable in 'summa'
hs = -summa['iLayerHeight'].isel(ifcToto=nSnow)

# Apply the condition 'layer_height > 0' and sum the result
snow_on = (hs > 0).sum()

# Apply the conditions and count the number of timesteps where both conditions are true
isothermal_days = ((hs > 0) & (average > 273.15)).sum().item()

# Append netcdf
ds = xr.open_dataset('/home/cdalden/summa_setup/analysis/crust_stats_ski_snotels_vJan8.nc')

# Split the string at the underscores
parts = out_name.split("_")

# Extract the parts
site = parts[0]
model_run = parts[1]

# Extract the year and convert it to a datetime
year_str = parts[2][2:]  # Remove the 'WY' prefix
year = int(year_str) + 2000  # Convert to an integer and add 2000
date = datetime.datetime(year, 1, 1)  # Create a datetime object for the first day of the year


# Check if the site does not exist in the dataset
if site not in ds.coords['site'].values:
    # Create a new dataset with all values set to nan
    new_ds = xr.Dataset()
    for var in ds.data_vars:
        # Create a new array filled with nan, with the same dimensions as the original data
        new_shape = [len(ds.coords[dim]) if dim != 'site' else 1 for dim in ds[var].dims]
        new_data = np.full(new_shape, np.nan)
        new_ds[var] = (ds[var].dims, new_data)

    # Set the site coordinate to the new site
    new_ds = new_ds.assign_coords(site=[site])

    # Concatenate the new dataset with the existing one along the 'site' dimension
    ds = xr.concat([ds, new_ds], dim='site')
    
# Assign a value to the 'crust_days' variable at the specified coordinates
ds['crust_days'].loc[dict(time=date, model_run=model_run, site=site)] = crust_days

# Assign a value to the 'mean_crusts' variable at the specified coordinates
ds['mean_crusts'].loc[dict(time=date, model_run=model_run, site=site)] = mean_crusts

# Assign a value to the 'crusts_binary' variable at the specified coordinates
ds['crusts_binary'].loc[dict(time=date, model_run=model_run, site=site)] = crusts_binary
print('number of crust days:' + str(crusts_binary/24)) # to make sure stats are working

# Assign a value to the 'snow_on' variable at the specified coordinates
ds['snow_on'].loc[dict(time=date, model_run=model_run, site=site)] = snow_on

# Assign a value to the 'snow_on' variable at the specified coordinates
ds['isothermal_days'].loc[dict(time=date, model_run=model_run, site=site)] = isothermal_days

temp_file = '/home/cdalden/summa_setup/crust_stats_ski_snotels_temp.nc'
ds.to_netcdf(temp_file, mode='w')
os.rename(temp_file, '/home/cdalden/summa_setup/analysis/crust_stats_ski_snotels_vJan8.nc')