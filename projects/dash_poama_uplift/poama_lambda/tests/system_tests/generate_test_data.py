import xarray as xr
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt


def generate_test_data():
    N_T=30
    N_X=100
    N_Y=100

    temp = 15 + 8 * np.random.rand(N_X, N_Y, N_T)
    precip = 10 * np.random.rand(N_X, N_Y, N_T)

    ds = xr.Dataset(
        {
            "temperature": (["x", "y", "time"], temp),
            "precipitation": (["x", "y", "time"], precip)
        },
        coords={
            "x": np.arange(0, N_X),
            "y": np.arange(0, N_Y),
            "time": pd.date_range("2020-01-01", periods=30)
        }
    )

    # -- to output on host machine
    # ds.to_netcdf("./test_data/poama_lambda_test_data.nc")

    # -- to output via shared docker volume
    ds.to_netcdf("/tmp/test_data/poama_lambda_test_data.nc")
    return ds


def sample_plot(ds, xs, ys, var, time):
    """
        ds   - xarray.Dataset  - dataset containing data to plot
        xs   - (int, int)      - lower and upper bound of x to plot
        ys   - (int, int)      - lower and upper bound of y to plot
        var  - str             - temperature or precipitation
        time - str             - time slice to choose YYYY-mm-dd
    """
    # select data - this will come from http response
    da = ds[var]

    # bound shape to data size
    xs[0] = int(np.max([xs[0], 0]))
    xs[1] = int(np.min([xs[1], da.shape[0]-1]))
    ys[0] = int(np.max([ys[0], 0]))
    ys[1] = int(np.min([ys[1], da.shape[1]-1]))

    da = da.sel(x=slice(xs[0],xs[1]), y=slice(ys[0],ys[1]), time=time)

    # plot heatmap
    # plt.pcolor(da)
    heatmap = plt.pcolor(da.T)

    # legend
    plt.colorbar(heatmap)

    # layout
    plt.xticks(range(0, da.shape[0], 5), da["x"].values[range(0, da.shape[0], 5)])
    plt.yticks(range(0, da.shape[1], 5), da["y"].values[range(0, da.shape[1], 5)])
    plt.subplots_adjust(left=0.15, right=0.99, bottom=0.15, top=0.90)

    # labels
    plt.ylabel("Y")
    plt.xlabel("X")
    plt.title("{} - {}".format(var, time))

    # save figure

    # -- to output on host machine
    # plt.savefig("./test_data/test_plot.png")

    # -- to output via shared docker volume
    plt.save_fig("/tmp/test_data/test_plot.png")


if __name__ == '__main__':
    ds = generate_test_data()
    sample_plot(ds, xs=[20, 50], ys=[10, 60], var="temperature",
        time="2020-01-05")

