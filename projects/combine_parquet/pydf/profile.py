import time
import pydf
import pandas as pd
import tabulate

INPUT_DIR_10_MIN = r"/scratch/eu56/nr4547/outputs-cc-sr/ten-mins-parquet-extracted-testing"

def profile():
    start = time.time()
    res = query()
    end = time.time()
    print(f"query = {end - start} seconds")

    start = time.time()
    df = pd.DataFrame(res.inner)
    print(df.describe())
    end = time.time()
    print(f"describe = {end - start} seconds")

    for v in ["air_temp", "dwpt"]:
        start = time.time()
        hist_ = histogram(df[v])
        skew_ = score_skewness(df[v])
        kurt_ = score_kurtosis(df[v])
        end = time.time()
        print_results(hist_, skew_, kurt_, v)
        print(f"{v}: {end - start} seconds")

def query():
    query_ = \
r"""
SELECT
    stn_num,
    air_temp,
    dwpt
FROM
    input_table
WHERE STN_NUM = '87113'
"""
    res = pydf.pydf_run_query(
        query_,
        INPUT_DIR_10_MIN,
        r"input_table",
        r"parquet",
        False,
        None,
        None
    )
    return res

def score_skewness(x):
    return pydf.pydf_kurtosis_1d(x.values)

def score_kurtosis(x):
    return pydf.pydf_skewness_1d(x.values)

def histogram(x):
    return pydf.pydf_hist_1d(x.values, 20)

def print_results(hist_, skew_, kurt_, v_):
    print("+" + "-" * 50)
    print("| HISTOGRAM")
    print(f"| >>> var = {v_}")
    print("+" + "-" * 50)
    print(tabulate.tabulate(hist_, headers=["start", "end", "count"], tablefmt="pipe"))
    print("+" + "-" * 50)
    print("| SCORES")
    print(f"| >>> var = {v_}")
    print("+" + "-" * 50)
    print(f"| kurtosis score = {kurt_}")
    print(f"| skewness score = {skew_}")
    print("+" + "=" * 50)
    
if __name__ == "__main__":
    profile()
