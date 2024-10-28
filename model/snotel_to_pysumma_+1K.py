# snotel = input('Enter the desired SNOTEL site code (ie. 1107:WA): ') + ':SNTL'
# water_year = int(input('Enter the water year: '))
# out_name = input('Enter the output file name (ie. buck_WY16): ')
out_name = 'quartzpeak_+1K_WY20'
# out_path = input('Enter the output path (ie. ../model/forcings/): ')
out_path = '/home/cdalden/summa_setup/model/forcings/'

# %%
import warnings
# pysumma has many depreciated packages, this ignores their warnings
warnings.filterwarnings("ignore", category=UserWarning, module='scipy')

from datetime import datetime, timedelta
from metloom.pointdata import SnotelPointData
import pandas as pd
import geopandas as gpd
import xarray as xr
from metsim import MetSim
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


import sys
sys.path.append('/home/cdalden/summa_setup/model')
from utils import lw_clr
from utils import forcing_filler as ff
from utils import summa_check as sc

# Read in current climate run for the site
current_climate_forcing_file = out_name.replace('+1K', 'current')
current_climate_forcing = xr.open_dataset(f'/home/cdalden/summa_setup/model/forcings/{current_climate_forcing_file}.nc')

data = current_climate_forcing.to_dataframe()

# Generate relative humidity assuming T_d is overnight low temperature
# Used to calculate specific humidity and longwave radiation
ff.fill_rel_hum(data)

# Simulated warming
data['airtemp'] = data['airtemp'] + 1 #K

# Generate pressure from hypsometric equation and site elevation (1981m)
ff.fill_pressure(data, 2000)

# Generate specific humidity
ff.fill_spec_hum(data)
data['spechum'] = data['spechum'].clip(lower=0.001)

# Generate longwave radiation
data['LWRadAtm'] = lw_clr.dilleyobrien1998(data['airtemp'], data['rh'])

data.reset_index(inplace=True)
data.set_index('time', inplace=True)

# Drop unnecessary columns
data = data.drop(columns=['rh', 'hru', 'gap_filled', 'data_step', 'hruId'])

# Interpolate the missing values
data.interpolate(inplace=True)

# %%
# Load template forcing file to preserve attributes
template = xr.open_dataset('./summa_forcing_template.nc')

# Convert dataframe to xarray
dsx = data.to_xarray()

# Loop through variables and add attributes from template forcing file
for data_var in dsx:
    dsx[data_var].attrs = template[data_var].attrs
    
# Add hru dimension
dsx = dsx.expand_dims(dim={'hru':1})

# Add gap-filled and datastep variables
dsx['gap_filled'] = xr.DataArray(np.ones((1,dsx.time.shape[0])),dims = ['hru','time'])
dsx['data_step'] = 3600 # 3600 seconds for 1hr timesteps

# Convert all to float64
for var in dsx.data_vars:
    dsx[var] = dsx[var].astype(np.float64)

# Set hruID based on template
dsx['hruId'] = (xr.DataArray(np.ones((1))*template['hruId'].values,dims = ['hru'])).astype(np.int32)

# Transpose all variables to match SUMMA dimensions
count = 0
for var in dsx.data_vars:
    # print(var,count)
    count += 1
    if count <= 7:
        attribs = dsx[var].attrs
        arr_t = dsx[var].values.T
        dsx[var] = xr.DataArray(dims = ['time','hru'],data = arr_t)
        dsx[var].attrs = attribs

# Set hruID based on template
dsx['hruId'] = (xr.DataArray(np.ones((1))*template['hruId'].values,dims = ['hru'])).astype(np.float64).fillna(0).astype(np.int32)

# Set time to match SUMMA format and save
dsx.to_netcdf(out_path+out_name+'.nc',
                        encoding = {"time":
                                        {'dtype' : 'float64',
                                         'units' : 'hours since 1990-01-01 00:00:00',
                                         'calendar' : 'standard'}})



# %%
