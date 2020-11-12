#!/usr/bin/env python
#-------------------------------------------------------------------------------
# Here is a quick script that plots a GC2 Ocean file without artefacts
# Credit and original Author: Griffith Young
#-------------------------------------------------------------------------------

import os
import time
import functools
import matplotlib as mpl
import matplotlib.pyplot as plt
import netCDF4 as nc
import numpy as np
import cartopy.crs as ccrs
import xarray as xr
from memory_profiler import profile


NC_FILENAME = "s_moa_sst_20201107_e01.nc"
OPENDAP_URI = "http://opendap.bom.gov.au:8080/thredds/dodsC/seasonal_prediction/access-s/ocean/sst/e01/{}".format(NC_FILENAME)
_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_NC = os.path.join(_DIR, 'test_data', NC_FILENAME)


def _benchmark(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        print('--- {}: start ---'.format(f.__name__))
        ts = time.time()

        r = f(*args, **kwargs)

        te = time.time()
        td = te - ts
        print('>>> {}: time taken = {}s'.format(f.__name__, td))
        print('--- {}: end ---'.format(f.__name__))
        return r
    return wrapper


@_benchmark
def ocean_plate_swap(plate, plus=False):
    # with xarray this actually modifies the original dataset too (i.e. the
    # copy of it that is loaded to memory - not a copy). xarray never modifies
    # the original data source (in opendap for example)

    # slice returns a view rather than copy
    slab1 = (slice(None), slice(722))
    slab2 = (slice(None), slice(720,1442))
    new_plate = np.empty(plate.shape)
    new_plate[slab1] = plate[slab2].values
    tmp_plate = np.empty(plate[slab1].shape)
    tmp_plate = plate[slab1].values
    if plus:
        tmp_plate[tmp_plate < 0.0] += 360
    new_plate[slab2] = tmp_plate
    return new_plate


@_benchmark
def go(lat, lon, val, sub, fn):
    ax = plt.axes((0.05, 0, 0.90, 1), projection=ccrs.PlateCarree())
    ax.pcolormesh(lon[sub], lat[sub], val[sub], transform=ccrs.PlateCarree())
    ax.set_xticks(range(-180, 181, 60))
    ax.set_xticklabels(['0','60W', '120W','180', '120E', '60E', '0'])
    ax.set_yticks(range(-60, 91, 30))
    ax.set_yticklabels(['60S', '30S', '0','30N', '60N', '90N'])
    ax.tick_params(top=True, labeltop=True)
    ax.tick_params(right=True, labelright=True)
    ax.grid(alpha=0.25)
    ax.coastlines()
    ax.set_title('Ocean Monitoring for ACCESS-S2')
    # ax.set_title('Ocean Monitoring for ACCESS-S2', pad=30.0)
    plt.savefig(fn, dpi=90)
    plt.close()


@_benchmark
def plot_lat_lon_vs_x2_y2(lat, lon, fn):
    swap_mat = np.empty(lat.shape)
    slab1 = (slice(None), slice(722))
    slab2 = (slice(None), slice(720,1442))

    swap_mat[slab1] = 0
    swap_mat[slab2] = 1
    
    plt.scatter(
        np.ravel(lon)[::100],
        np.ravel(lat)[::100],
        s=0.1,
        c=np.ravel(swap_mat)[::100]
    )
    plt.savefig(fn, dpi=90)
    plt.close()


@_benchmark
def plot_slice_where(da, fn):
    lon_range = [-180, 179]
    lat_range = [-100, 100]
    data = get_slice_where(da, lat_range, lon_range)
    ax = plt.axes((0.05, 0, 0.90, 1), projection=ccrs.PlateCarree())
    ax.pcolormesh(data.nav_lon, data.nav_lat, data, transform=ccrs.PlateCarree())
    ax.coastlines()
    plt.savefig(fn, dpi=90)
    plt.close()


@_benchmark
def get_slice_where(da, lat_range, lon_range):
    da_sliced = da.where(
        ((da.nav_lon >= lon_range[0]) &
        (da.nav_lon <= lon_range[1]) &
        (da.nav_lat >= lat_range[0]) &
        (da.nav_lat <= lat_range[1])),
        drop=True
    )
    return da_sliced


@_benchmark
def get_slice(da, x_1_slice, y_2_slice):
    return da[y_2_slice, x_1_slice]
    

@_benchmark
@profile
def profile_only_where_small_local():
    with xr.open_dataset(LOCAL_NC) as ds:
        data = get_slice_where(ds.temp[0, 0], [-60, -55], [-150, -145])
        data.values


@_benchmark
@profile
def profile_only_where_small_opendap():
    with xr.open_dataset(OPENDAP_URI) as ds:
        data = get_slice_where(ds.temp[0, 0], [-60, -55], [-150, -145])
        data.values


@_benchmark
@profile
def profile_only_where_large_local():
    with xr.open_dataset(LOCAL_NC) as ds:
        data = get_slice_where(ds.temp[0, 0], [-50, 50], [60, 80])
        data.values


@_benchmark
@profile
def profile_get_slice_small_local():
    with xr.open_dataset(LOCAL_NC) as ds:
        data = get_slice(ds.temp[0, 0], slice(10,20), slice(10,20))
        data.values

@_benchmark
@profile
def profile_get_slice_small_opendap(xs=None, ys=None):
    if xs is None:
        xs = slice(10,20)
    if ys is None:
        ys = slice(10,20)
    with xr.open_dataset(OPENDAP_URI) as ds:
        data = get_slice(ds.temp[0, 0], xs, ys)
        data.values


@_benchmark
@profile
def profile_get_slice_large_local():
    with xr.open_dataset(LOCAL_NC) as ds:
        data = get_slice(ds.temp[0, 0], slice(None), slice(None))
        data.values


@_benchmark
@profile
def profile_only_swap_local():
    with xr.open_dataset(LOCAL_NC) as ds:
        print("swap lat")
        lat = ocean_plate_swap(ds['nav_lat'][:])
        print("swap lon")
        lon = ocean_plate_swap(ds['nav_lon'][:], True)
        print("swap sst")
        sst = ocean_plate_swap(ds['temp'][0, 0][:])


@profile
def dummy_load_local():
    with xr.open_dataset(LOCAL_NC) as ds:
        pass


@profile
def main():
    if os.path.exists(LOCAL_NC):
        f = LOCAL_NC
    else:
        f = OPENDAP_URI
    with xr.open_dataset(f) as ds:
        plt.rcParams.update({'figure.figsize': [16, 8], 'axes.titlepad': 36.0})

        sub=(slice(None), slice(None))

        print("=== plot using swap ===")
        print("swap lat")
        lat = ocean_plate_swap(ds['nav_lat'][:])
        print("swap lon")
        lon = ocean_plate_swap(ds['nav_lon'][:], True)
        print("swap sst")
        sst = ocean_plate_swap(ds['temp'][0, 0][:])
        go(lat, lon, sst, sub, 'open_dap_test_swap.png')

        print("=== plot using 'where' ===")
        plot_slice_where(ds.temp[0, 0][:], 'open_dap_test_where.png')


#-------------------------------------------------------------------------------

if __name__ == '__main__':
    # === local tests ===

    # run initial to prevent lazy loading
    # dummy_load(_local)

    # --- run these one at a time because xarray likes to keep data in memory
    # --- where possible
    # profile_only_swap_local()

    # profile_only_where_small_local()
    # profile_only_where_large_local()

    # profile_get_slice_small_local()
    # profile_get_slice_large_local()

    # === opendap tests ===
    # profile_only_where_small_opendap()
    for slices in [
            (slice(10,100), slice(10, 100)),
            (slice(100,400), slice(100, 400)),
            (slice(400,None), slice(400, None)) ]:
        profile_get_slice_small_opendap(slices[0], slices[1])

"""
Notes:
    - using `where` using (lat, lon) loads entire data into memory and is slow
      depending on which part of the data you choose.
    - using slicing is a more memory efficient and also faster but is less
      intuitive since you have to convert lat-lon to grid coordinates. Will
      need a KDTree to do this efficiently.
    - eitherway, we need to perform the `swap` otherwise we will have artefacts
    - for opendap, swap will cause it to load the data ~14MB [30MB
      uncompressed] for a particular datetime/depth. opendap download speeds
      are slow, but not too bad for small slices:
        - 100 x 100 slice 1-1.5s
        - 300 x 300 slice 3-5s
        - 600 x 1000 slice ~16s
    - using `where` with opendap is always a bad idea
    - I think KDTree to map lat/lon to x_2/y_2 is the best way forward since we
      are using slicing
"""
#-------------------------------------------------------------------------------
