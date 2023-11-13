import pydf
import pprint
import tabulate
import pandas as pd
import matplotlib.pyplot as plt

def stats():
    query = r"""
SELECT * FROM input_table
WHERE stn_num = 32197
ORDER BY time_rsmpl
"""
    out = pydf.pydf_run_query(
        query,
        r"/home/nvr90/test_pydf/parquet/",
        r"input_table",
        r"parquet",
        False,
        None,
        None
    )
    df = pd.DataFrame(out.inner)
    df.set_index("time_rsmpl")

    # histogram
    for k in df.keys():
        if k == "time_rsmpl" or k == "stn_num":
            continue
        h = pydf.pydf_hist_1d(df[k].values, 20)
        print("+" + "-" * 99)
        print("| HISTOGRAM")
        print(f"| >>> var = {k}")
        print("+" + "-" * 99)
        print(tabulate.tabulate(h, headers=["start", "end", "count"], tablefmt="pipe"))
        print("+" + "-" * 99)
        print("| SCORES")
        print(f"| >>> var = {k}")
        print("+" + "-" * 99)
        k_score = pydf.pydf_kurtosis_1d(df[k].values)
        s_score = pydf.pydf_skewness_1d(df[k].values)
        print(f"| kurtosis score = {k_score}")
        print(f"| skewness score = {s_score}")
        print("+" + "=" * 99)
    # kurtosis of each variable

    
def sample_query():
    # df_run_query(q, input_path, input_table_name, data_format, preview_only, output_path=None, output_table_name=None)
    out = pydf.pydf_run_query(
        r"""
SELECT
    stn_num STRING,
    AVG(air_temp) :: DOUBLE AS air_temp,
    AVG(dwpt) :: DOUBLE AS dwpt,
    date_part('month', time_rsmpl) :: BIGINT AS month
FROM input_table
WHERE air_temp IS NOT NULL
        AND dwpt IS NOT NULL
        AND stn_num = 32197
GROUP BY month, stn_num
ORDER BY month;
""",
        r"/home/nvr90/test_pydf/parquet/",
        r"input_table",
        r"parquet",
        False,
        None,
        None
    )

    df = pd.DataFrame(out.inner)

    df.plot(x="month", subplots=True)
    # Save figure
    plt.savefig('/mnt/d/temp_plot.pdf')
  

if __name__ == "__main__":
    # sample_query()
    stats()
