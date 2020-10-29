import io
import boto3
import xarray as xr

# NOTE: do not over use this function as it can incur costs after downloads >
# 1GB. Using it within lambda is safe if deployed in the same region.


# TODO: these settings are hardcoded in multiple places
BUCKET_NAME = 'sam-poama-netcdf-test-data'
OBJ_TEST_DATA = 'test_data/poama_lambda_test_data.nc'
PROFILE_NAME = 'sam_deploy'


def get_s3_test_dataset():
    session = boto3.Session(profile_name=PROFILE_NAME)
    s3 = session.client('s3')

    nc_buffer = io.BytesIO()
    s3.download_fileobj(BUCKET_NAME, OBJ_TEST_DATA, nc_buffer)
    nc_buffer.seek(0)

    # write out file for checking
    with xr.open_dataset(nc_buffer, engine='h5netcdf') as ds:
        ds.to_netcdf('test.nc')


def read_downloaded_netcdf():
    with xr.open_dataset('test.nc') as ds:
        print(ds)
    

if __name__ == '__main__':
    # Commented out to prevent accidental download.
    # get_s3_test_dataset()
    read_downloaded_netcdf()
