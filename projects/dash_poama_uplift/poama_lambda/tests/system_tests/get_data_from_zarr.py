import os
import time
import functools
import s3fs
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
# s3 store = s3://fvt-test-zarr-nr/test_zarr_store.zarr
S3_STORE = 'fvt-test-zarr/test_zarr_store.zarr'
AWS_REGION = 'ap-southeast-2'


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
def slice_data(da, xs, ys, is_zarr=False):
    if is_zarr:
        return da[0, 0, ys, xs]
    else:
        return da[0, 0, ys, xs].values


@_benchmark
def get_local_fs_store():
    store = DirectoryStore(ZARR_PATH)
    return store


@_benchmark
def get_s3_store():
    s3 = s3fs.S3FileSystem(
        anon=False,
        client_kwargs=dict(region_name=AWS_REGION)
    )
    store = s3fs.S3Map(root=S3_STORE, s3=s3, check=False)
    return store


@_benchmark
@profile
def dump_xarray_as_zarr_local_fs():
    fs_store = DirectoryStore(ZARR_PATH)
    with xr.open_dataset(NC_PATH) as ds:
        ds_chunked = chunk_dataset(ds)
        # overwrite if exists
        ds_chunked.to_zarr(fs_store, mode="w")


@_benchmark
@profile
def dump_zarr_to_s3():
    s3_store = get_s3_store()

    with xr.open_dataset(NC_PATH) as ds:
        ds_chunked = chunk_dataset(ds)
        # overwrite if exists
        ds_chunked.to_zarr(s3_store, mode="w")


@_benchmark
def slice_using_xarray(store, xs, ys):
    with xr.open_zarr(store) as ds:
        data = slice_data(ds.temp, xs, ys, is_zarr=False)
        return data


@_benchmark
def slice_using_zarr(store, xs, ys):
    # note: no need to explictly call close
    z = zarr.open_group(store, mode='r')
    data = slice_data(z.temp, xs, ys, is_zarr=True)
    return data


@_benchmark
@profile
def read_zarr_slice_from_s3(xs=None, ys=None, load_using_zarr=False):
    ys = slice(0, 500) if ys is None else ys
    xs = slice(0, 500) if xs is None else xs
    print('xs = {}, ys = {}'.format(xs, ys))

    s3_store = get_s3_store()

    if load_using_zarr:
        data = slice_using_zarr(s3_store, xs, ys)
    else:
        data = slice_using_xarray(s3_store, xs, ys)

    plt.imshow(data)
    fn = 'test_zarr{}.png'.format('' if load_using_zarr else '_xarray')
    plt.savefig(fn)
    plt.close()


@_benchmark
@profile
def read_zarr_slice_from_local_fs(xs=None, ys=None, load_using_zarr=False):
    ys = slice(0, 500) if ys is None else ys
    xs = slice(0, 500) if xs is None else xs
    print('xs = {}, ys = {}'.format(xs, ys))

    fs_store = get_local_fs_store()

    if load_using_zarr:
        data = slice_using_zarr(fs_store, xs, ys)
    else:
        data = slice_using_xarray(fs_store, xs, ys)

    plt.imshow(data)
    fn = 'test_zarr{}.png'.format('' if load_using_zarr else '_xarray')
    plt.savefig(fn)
    plt.close()


def main():
    # !!! run one at a time to get more accurate memory profiles
    # read_zarr_directly_local_fs()
    # read_xarray_from_zarr_local_fs()
    # dump_xarray_as_zarr_local_fs()
    xs = slice(0, 200)
    ys = slice(0, 200)
    read_zarr_slice_from_local_fs(xs, ys, load_using_zarr=False)


if __name__ == '__main__':
    main()

