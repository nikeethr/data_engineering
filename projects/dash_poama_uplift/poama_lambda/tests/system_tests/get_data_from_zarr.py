import os
import time
import functools
import zarr
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt

from zarr.storage import DirectoryStore
from memory_profiler import profile


"""
    Notes:
        - Two types of stores: `store` and `chunk_store`. The latter is if you
          want the chunks to be stored in a different storage type.
        - Zarr auto chunks things, but we can use Dataset.chunk to do the
          chunking based on what we know. Note: requires `dask` and `toolz`
        - Zarr data loading is extremely lazy, and aggregation operations (with
          numpy) are chunked too because of dask. I had to use imshow() which
          required the entire dataset to force it to load the specified slice.
          This is a good thing.
        - For xarray you can force load to memory using `.values`
"""

_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(_DIR, 'test_data')
NC_PATH = os.path.join(TEST_DIR, 's_moa_sst_20201107_e01.nc')
ZARR_PATH = os.path.splitext(NC_PATH)[0] + '.zarr'


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
def chunk_dataset(ds):
    # chunk assuming we will only query 1 time instance
    # only chunking dimensions associated with temp. ignoring others.
    return ds.chunk(chunks={
        "x_2": 100,
        "y_2": 100, 
        "time_counter": 1
    })


@_benchmark
@profile
def dump_xarray_as_zarr_local_fs():
    fs_store = DirectoryStore(ZARR_PATH)
    with xr.open_dataset(NC_PATH) as ds:
        ds_chunked = chunk_dataset(ds)
        # overwrite if exists
        ds_chunked.to_zarr(fs_store, mode="w")

@_benchmark
def slice_data(da, xs, ys, is_zarr=False):
    if is_zarr:
        return da[0, 0, ys, xs]
    else:
        return da[0, 0, ys, xs].values

@_benchmark
@profile
def read_zarr_directly_local_fs(xs=None, ys=None):
    # note: no need to explictly call close
    z = zarr.open(ZARR_PATH, mode='r')

    ys = slice(0, 500)
    xs = slice(0, 500)
    
    data = slice_data(z.temp, xs, ys, is_zarr=True)

    plt.imshow(data)
    plt.savefig('test_zarr.png')
    plt.close()


@_benchmark
@profile
def read_xarray_from_zarr_local_fs(xs=None, ys=None):
    fs_store = DirectoryStore(ZARR_PATH)
    with xr.open_zarr(fs_store) as ds:

        ys = slice(0, 500)
        xs = slice(0, 500)

        data = slice_data(z.temp, xs, ys, is_zarr=False)

        plt.imshow(da)
        plt.savefig('test_zarr_xarray.png')
        plt.close()



def main():
    # !!! run one at a time to get more accurate memory profiles
    # dump_xarray_as_zarr_local_fs()
    read_zarr_directly_local_fs()
    # read_xarray_from_zarr_local_fs()



if __name__ == '__main__':
    main()

