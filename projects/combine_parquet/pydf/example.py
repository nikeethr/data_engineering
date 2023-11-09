import pydf
import pprint
import pandas as pd
import matplotlib.pyplot as plt

def main():
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
    main()
