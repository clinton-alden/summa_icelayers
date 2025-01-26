import numpy as np
import pandas as pd
import xarray as xr
import datetime
import os

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

run_name = input("Enter the run name: ")
# print('**********')
print(run_name)
print('**********')
summa = xr.open_dataset('/home/cdalden/summa_setup/model/output/output_'+run_name+'_timestep.nc')

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
max_depth = summa.isel(hru=0)['iLayerHeight'].max(dim='ifcToto') - 1
filtered_var = filtered_var.where(summa.isel(hru=0)['iLayerHeight'] > max_depth)

# don't need a minimum density value, did not have significant impact on accuracy of algorithm
# rho_min = 0.27
# filtered_var = filtered_var.where(filtered_var > rho_min)

# Calculate the vertical derivative
derivative = filtered_var.diff(dim='midToto')

# Initialize an empty list to store the counts
counts = []

# Loop over the 'time' dimension
for t in var.time.values:
    # Select the derivative for the current timestep
    derivative_t = derivative.sel(time=t)

    # Filter values that are greater than or equal to 0.2 or less than or equal to -0.2
    threshold = 0.05
    # filtered = derivative_t.where((derivative_t >= threshold) | (derivative_t <= threshold))
    filtered = derivative_t.where(derivative_t >= threshold)

    # Count the number of layers with at least one such value
    count = np.isfinite(filtered).sum().values

    # Append the count to the list
    counts.append(count)

# Convert the list to a numpy array
counts = np.array(counts)

crust_days = counts.sum()/24
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
ds = xr.open_dataset('/home/cdalden/summa_setup/analysis/crust_stats_harts.nc')

# Split the string at the underscores
parts = run_name.split("_")

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

# Assign a value to the 'snow_on' variable at the specified coordinates
ds['snow_on'].loc[dict(time=date, model_run=model_run, site=site)] = snow_on

# Assign a value to the 'snow_on' variable at the specified coordinates
ds['isothermal_days'].loc[dict(time=date, model_run=model_run, site=site)] = isothermal_days

temp_file = '/home/cdalden/summa_setup/crust_stats_temp_harts.nc'
ds.to_netcdf(temp_file, mode='w')
os.rename(temp_file, '/home/cdalden/summa_setup/analysis/crust_stats_harts.nc')