import os
import xarray as xr

DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(DIR, 'sample_data')
SAMPLE_FC_FILE = os.path.join(
    DATA_DIR,
    'ovens_example',
    'SWIFT-Ensemble-Forecast-Flow_ovens_20200929_2300.nc'
)

def process():
    # decode_times = False because "hours since time of forecast" is not
    # recognizable
    # - parse time from file
    # - parse catchment from file
    # - load station metadata to get node_id
    # - use node id to get station_id
    # - calculate quartiles
    # - populate table
    with xr.open_dataset(SAMPLE_FC_FILE, decode_times=False) as ds:
        print(ds)
        pass

if __name__ == '__main__':
    process()
