#!/usr/bin/env python
#-------------------------------------------------------------------------------
# Here is a quick script that plots a GC2 Ocean file without artefacts
# Credit and original Author: Griffith Young
#-------------------------------------------------------------------------------

import matplotlib as mpl
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import cartopy.crs as ccrs
import xarray as xr


OPENDAP_URI = "http://opendap.bom.gov.au:8080/thredds/dodsC/seasonal_prediction/access-s/ocean/sst/e01/w_doa_sst_20201024_e01.nc"
LOCAL_NC = "local_test_nc.nc"


def ocean_plate_swap(plate, plus=False):
    slab1 = (slice(None), slice(722))
    slab2 = (slice(None), slice(720,1442))
    new_plate = np.empty(plate.shape)
    new_plate[slab1] = plate[slab2]
    tmp_plate = np.empty(plate[slab1].shape)
    tmp_plate = plate[slab1]
    if plus:
        tmp_plate[tmp_plate < 0.0] += 360
    new_plate[slab2] = tmp_plate
    return new_plate


def go(lat, lon, val, sub):
    ax = plt.axes((0.05, 0, 0.90, 1), projection=ccrs.PlateCarree(central_longitude=180))
    ax.pcolormesh(lon[sub], lat[sub], val[sub], transform=ccrs.PlateCarree())
    ax.set_xticks(range(-180, 181, 60))
    ax.set_xticklabels(['0','60W', '120W','180', '120E', '60E', '0'])
    ax.set_yticks(range(-60, 91, 30))
    ax.set_yticklabels(['60S', '30S', '0','30N', '60N', '90N'])
    ax.tick_params(top=True, labeltop=True)
    ax.tick_params(right=True, labelright=True)
    ax.grid(alpha=0.25)
    ax.set_title('Ocean Monitoring for ACCESS-S2')
    # ax.set_title('Ocean Monitoring for ACCESS-S2', pad=30.0)
    plt.savefig('open_dap_test.png')
    plt.close()


def main():
    f = OPENDAP_URI
    with xr.open_dataset(f) as ds:
        if f == OPENDAP_URI:
            ds.to_netcdf(LOCAL_NC)
            return
        lat = ocean_plate_swap(ds['nav_lat'][:])
        lon = ocean_plate_swap(ds['nav_lon'][:], True)
        sst = ocean_plate_swap(ds['temp'][0, 0][:])

        sub=(slice(None), slice(None))

        plt.rcParams.update({'figure.figsize': [16, 8], 'axes.titlepad': 36.0})

        go(lat, lon, sst, sub)


#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main()

#-------------------------------------------------------------------------------

