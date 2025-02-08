# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as datetime
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from metloom.pointdata import SnotelPointData
import geopandas as gpd

# %%
sntls = pd.read_csv('/home/cdalden/summa_setup/analysis/sntl_list_ski_temps_snowfrac.csv')

start_date = datetime(2000, 12, 1)
end_date = datetime(2024, 3, 31)

# Loop through the 'site' column and assign the corresponding 'state'
for index, row in sntls.iterrows():
    sntls = pd.read_csv('/home/cdalden/summa_setup/analysis/sntl_list_ski_temps_snowfrac.csv')
    site = row['site_code']
    state = row['state']
    print(row['site_name'])
    # %%
    # Pull desired variables from snotel to dataframe
    # snotel_point = SnotelPointData(snotel, "MyStation")
    snotel_point = SnotelPointData(f'{str(site)}:{str(state)}:SNTL', "MyStation")
    df = snotel_point.get_hourly_data(
        start_date, end_date,
        [snotel_point.ALLOWED_VARIABLES.PRECIPITATIONACCUM, snotel_point.ALLOWED_VARIABLES.TEMP]
    )

    # Clean up the dataframe
    df.reset_index(inplace=True)

    # Rename columns
    replace = {'ACCUMULATED PRECIPITATION':'accppt','AIR TEMP':'airtemp', 'datetime':'time'}
    df.rename(columns=replace, inplace=True)
    df.set_index('time', inplace=True)
    # conver airtemp to C
    df['airtempC'] = (df['airtemp'] - 32) * 5/9

    # Currier snotel temp correction
    df['airtempC'] = (1.03*(df['airtempC']-0.9))

    # calc precip rate
    df['precip'] = df['accppt'].diff()

    # %%
    # Function to filter rows between December 1 and March 31
    def is_winter_month(date):
        return (date.month == 12 or date.month == 1 or date.month == 2 or date.month == 3)

    # Filter the DataFrame
    winter_df = df[df.index.map(is_winter_month)]

    # Calculate total snow and rain for the winter months with different thresholds
    def calculate_snow_rain_fractions(df, threshold):
        snow = df.loc[df['airtempC'] < threshold, 'precip'].sum()
        rain = df.loc[df['airtempC'] >= threshold, 'precip'].sum()
        snow_frac = snow / (snow + rain) * 100 if (snow + rain) > 0 else 0
        return snow, rain, snow_frac

    # Thresholds
    thresholds = [0, -2, -4]
    column_names = ['snow_precip_frac', 'snow_precip_frac_2C', 'snow_precip_frac_4C']

    # Calculate and assign results for each threshold
    for threshold, column_name in zip(thresholds, column_names):
        snow, rain, snow_frac = calculate_snow_rain_fractions(winter_df, threshold)
        sntls.loc[sntls.site_code == site, column_name] = np.round(snow_frac, 2)
        print(f"Threshold: {threshold}°C")
        print(f"Total snow: {snow}")
        print(f"Total rain: {rain}")
        print(f"Fraction of precip that is snow: {snow_frac:.2f}%\n")
    
    sntls.to_csv('/home/cdalden/summa_setup/analysis/sntl_list_ski_temps_snowfrac.csv', index=False)

# %%



