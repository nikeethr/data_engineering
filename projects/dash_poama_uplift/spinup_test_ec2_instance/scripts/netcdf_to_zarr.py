import os
import glob
import functools
import time
import argparse
import logging
import xarray as xr
import zarr
from zarr.storage import DirectoryStore


LOGGER = logging.getLogger(__name__)

def _benchmark(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        LOGGER.info('--- {}: start ---'.format(f.__name__))
        ts = time.time()

        r = f(*args, **kwargs)

        te = time.time()
        td = te - ts
        LOGGER.info('>>> {}: time taken = {}s'.format(f.__name__, td))
        LOGGER.info('--- {}: end ---'.format(f.__name__))
        return r
    return wrapper


# TODO: This needs to be more generic for unknown file formats...?
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
def dump_xarray_as_zarr_local_fs(nc_path, zarr_dir):
    zarr_path = os.path.join(
        zarr_dir, os.path.splitext(os.path.basename(nc_path))[0] + '.zarr')
    fs_store = DirectoryStore(zarr_path)
    with xr.open_dataset(nc_path) as ds:
        ds_chunked = chunk_dataset(ds)
        # overwrite if exists
        ds_chunked.to_zarr(fs_store, mode="w")
        # consolidate metadata for faster read.
        # NOTE: This means the file will be only usable as read-only
        zarr.consolidate_metadata(fs_store)


def parse_args():
    LOGGER.info("parsing args...")
    parser =argparse.ArgumentParser(description=(
        'Convert netcdf files to consolidated (read-only) zarr format.'))
    parser.add_argument(
        'netcdf_in',
        type=str,
        help='input netcdf directory/file'
    )
    parser.add_argument(
        'zarr_out',
        type=str,
        help='output zarr directory'
    )
    args = parser.parse_args()
    return args


def main():
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    if not os.path.isdir(args.zarr_out):
        os.makedirs(args.zarr_out)
    if os.path.isdir(args.netcdf_in):
        nc_fns = glob.glob(os.path.join(args.netcdf_in, '*.nc'))
        for fn in nc_fns:
            LOGGER.info(f'processing: {fn}')
            dump_xarray_as_zarr_local_fs(fn, args.zarr_out)
    elif os.path.isfile(args.netcdf_in):
        LOGGER.info(f'processing: {args.netcdf_in}')
        dump_xarray_as_zarr_local_fs(args.netcdf_in, args.zarr_out)


if __name__ == '__main__':
    main()
