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

def test_hvplot_from_ds():
    with xr.open_dataset('test_data/s_moa_sst_20201107_e01.nc') as ds:
        ts = time.time()
        plot = ds.temp[0, 0, slice(0,100), slice(0,100)].hvplot.quadmesh(
            'nav_lon', 'nav_lat',
            crs=ccrs.PlateCarree(), projection=ccrs.PlateCarree(),
            project=True,
            geo=True,
            coastline=True,
            rasterize=True,
            frame_width=600,
            dynamic=False
        )
        print("dynamic plot: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        hvplot.save(plot, 'test_dynamic_plot.html')
        print("savfig: {:.3f}s".format(time.time() - ts))

def test_plot_from_ds():
    with xr.open_dataset('test_data/s_moa_sst_20201107_e01.nc') as ds:
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
        fn = 'test_static_plot.png'
        plt.savefig(fn, dpi=90)
        plt.close()
        print("savfig: {:.3f}s".format(time.time() - ts))

def test_plot_from_mpl():
    with xr.open_dataset('test_data/s_moa_sst_20201107_e01.nc') as ds:
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
        fn = 'test_static_plot.png'
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
    with xr.open_dataset('test_data/s_moa_sst_20201107_e01.nc') as ds:
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
        tf.shade(qm).to_pil().save('test_shader.png')
        print("quad mesh: {:.3f}s".format(time.time() - ts))

        ts = time.time()
        out_json = {
            'height': 168,
            'width': 360,
            'values': qm.values.ravel().astype(np.float32).tolist()
        }
        with open('ovt_data.json', 'w') as f:
            s = simplejson.dumps(out_json, ignore_nan=True)
            f.write(s)
        print("output json: {:.3f}s".format(time.time() - ts))


if __name__ == '__main__':
    # test_plot_from_ds()
    test_hvplot_from_ds()
    # test_data_shader()
