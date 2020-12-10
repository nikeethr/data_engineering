import os
import hvplot
import simplejson
import hvplot.xarray
import time
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import datashader
from memory_profiler import profile
from datashader import transfer_functions as tf, reductions as rd


_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(_DIR, 'test_data')
NC_PATH = os.path.join(TEST_DIR, 's_moa_sst_20201107_e01.nc')


def test_hvplot_from_ds():
    with xr.open_dataset(NC_PATH) as ds:
        ts = time.time()

        da = ds.temp[0, 0, slice(100,200), slice(200,600)]
        #y_idx, x_idx = np.where(
        #    np.abs(da.nav_lon[:, 1:] - da.nav_lon[:, 0:-1]) > 355)
        #for i, y in enumerate(y_idx):
        #    da.nav_lon[y, x_idx[i]:] += 360
        #print("slice: {:.3f}s".format(time.time() - ts))

        # swap
        # ts = time.time()
        # da = ds.temp[0, 0]
        # da = xr.concat([da[100:200, 600:], da[100:200, :200]], dim='x_2')
        # print("swap: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        plot = da.hvplot.quadmesh(
            'nav_lon', 'nav_lat',
            crs=ccrs.PlateCarree(), projection=ccrs.PlateCarree(180,),
            project=True,
            geo=True,
            coastline=True,
            rasterize=True,
            frame_width=600,
            dynamic=False,
            cmap='viridis',
        ).opts(
            toolbar='above'
        )
        print("dynamic plot: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        hvplot.save(plot, os.path.join(TEST_DIR, 'test_dynamic_plot.html'))
        print("savfig: {:.3f}s".format(time.time() - ts))

def test_plot_from_ds():
    with xr.open_dataset(NC_PATH) as ds:
        ts = time.time()
        plt.figure(figsize=(14,6))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_global()
        print("setup figure: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        p = ds.temp[0, 0].plot.pcolormesh(ax=ax, transform=ccrs.PlateCarree(),
            x='nav_lon', y='nav_lat', add_colorbar=True)
        print("colormesh: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        ax.coastlines()
        print("coastlines: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        ax.set_xticks(range(-180, 181, 60))
        ax.set_xticklabels(['0','60W', '120W','180', '120E', '60E', '0'])
        ax.set_yticks(range(-60, 91, 30))
        ax.set_yticklabels(['60S', '30S', '0','30N', '60N', '90N'])
        ax.tick_params(top=True, labeltop=True)
        ax.tick_params(right=True, labelright=True)
        ax.grid(alpha=0.25)
        ax.set_title('Ocean Monitoring for ACCESS-S2')
        print("setup axis: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        fn = os.path.join(TEST_DIR, 'test_static_plot.png')
        plt.savefig(fn, dpi=90)
        plt.close()
        print("savfig: {:.3f}s".format(time.time() - ts))

def test_plot_from_mpl():
    with xr.open_dataset(NC_PATH) as ds:
        ts = time.time()
        plt.figure(figsize=(14,6))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_global()
        print("setup figure: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        ax.pcolormesh(ds.nav_lon, ds.nav_lat, ds.temp[0, 0],
            transform=ccrs.PlateCarree())
        print("colormesh: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        ax.coastlines()
        print("coastlines: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        ax.set_xticks(range(-180, 181, 60))
        ax.set_xticklabels(['0','60W', '120W','180', '120E', '60E', '0'])
        ax.set_yticks(range(-60, 91, 30))
        ax.set_yticklabels(['60S', '30S', '0','30N', '60N', '90N'])
        ax.tick_params(top=True, labeltop=True)
        ax.tick_params(right=True, labelright=True)
        ax.grid(alpha=0.25)
        ax.set_title('Ocean Monitoring for ACCESS-S2')
        print("setup axis: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        fn = os.path.join(TEST_DIR, 'test_static_plot.png')
        plt.savefig(fn, dpi=90)
        plt.close()
        print("savfig: {:.3f}s".format(time.time() - ts))


# @profile
def test_data_shader():
    """
        This creates a `quadmesh` from the data array using the 2-D lat/lon
        coordinates. The resultant matrix can be used for raster layer on a
        map. For 1-d coordinates you can use `raster`.
        https://datashader.org/user_guide/Grids.html
    """
    with xr.open_dataset(NC_PATH) as ds:
        ts = time.time()
        da = ds.temp[0, 0]
        # da = da_.copy(deep=True)
        print("select data: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        canvas = datashader.Canvas(
            plot_width=360,
            plot_height=168
        )
        print("make canvas: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        qm = canvas.quadmesh(da, x='nav_lon', y='nav_lat')
        tf.shade(qm).to_pil().save(
            os.path.join(TEST_DIR, 'test_shader.png')
        )
        print("quad mesh: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        out_json = {
            'height': 168,
            'width': 360,
            'lat': qm.nav_lat.values.astype(np.float16).tolist(),
            'lon': qm.nav_lon.values.astype(np.float16).tolist(),
            'values': qm.values.ravel().astype(np.float16).tolist()
        }
        with open(os.path.join(TEST_DIR, 'ovt_data.json'), 'w') as f:
            s = simplejson.dumps(out_json, ignore_nan=True)
            f.write(s)
        print("output json: {:.3f}s".format(time.time() - ts))

# @profile
def test_data_shader_minimal():
    """
        Test for small dataset
    """
    Qy = [[1, 2, 4],
          [1, 2, 3],
          [1, 2, 3]]

    Qx = [[1, 1, 1],
          [2, 2, 2],
          [2.5, 3, 3]]

    Z = [[1, 2, 3],
         [4, 5, 6],
         [7, 8, 9]]

    da = xr.DataArray(Z, name='Z', dims = ['y', 'x'],
                      coords={'Qy': (['y', 'x'], Qy),
                              'Qx': (['y', 'x'], Qx)})

    ts = time.time()
    canvas = datashader.Canvas(plot_height=100, plot_width=100)
    qm = canvas.quadmesh(da, x='Qx', y='Qy')
    print("quad mesh: {:.3f}s".format(time.time() - ts))

if __name__ == '__main__':
    # test_plot_from_ds()
    # test_hvplot_from_ds()
    test_data_shader()
    # test_data_shader_minimal()
