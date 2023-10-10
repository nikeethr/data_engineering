use datafusion::dataframe::DataFrameWriteOptions;
use datafusion::prelude::*;
use std::fs::{DirBuilder, File};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tar::Archive;

// -------------------------------------------------------------------------------------------------
// Actual implementation
// -------------------------------------------------------------------------------------------------

#[tokio::main]
async fn resample_parquet_data(input_path: &Path) -> datafusion::error::Result<()> {
    let ctx = SessionContext::new();
    register_parquet_reader(input_path, &ctx).await?;
    resample_to_10_min(&ctx).await?;
    Ok(())
}

async fn register_parquet_reader(
    input_path: &Path,
    ctx: &SessionContext,
) -> datafusion::error::Result<()> {
    // ---
    // TODO: are these actually necessary?
    let mut parquet_options = ParquetReadOptions::default();
    parquet_options.file_extension = ".pq";
    // ---
    let str_input_path = input_path.to_str().unwrap();
    ctx.register_parquet("obs_table", &str_input_path, parquet_options)
        .await?;

    Ok(())
}

// fields
// obs_table.STN_NUM,obs_table.LSD,obs_table.DATE_CREATED,obs_table.LAST_UPDATE,obs_table.TM,obs_table.LCT,obs_table.OB_QUAL_FLAG,obs_table.WND_DIR,obs_table.WND_DIR_QUAL,obs_table.WND_DIR_SD,obs_table.WND_DIR_SD_QUAL,obs_table.WND_SPD,obs_table.WND_SPD_QUAL,obs_table.MAX_WND_GUST,obs_table.MAX_WND_GUST_QUAL,obs_table.MIN_WND_SPD,obs_table.MIN_WND_SPD_QUAL,obs_table.AIR_TEMP,obs_table.AIR_TEMP_QUAL,obs_table.WETB,obs_table.WETB_QUAL,obs_table.DWPT,obs_table.DWPT_QUAL,obs_table.AIR_TEMP_MAX,obs_table.AIR_TEMP_MAX_QUAL,obs_table.AIR_TEMP_MIN,obs_table.AIR_TEMP_MIN_QUAL,obs_table.WETB_MAX,obs_table.WETB_MAX_QUAL,obs_table.WETB_MIN,obs_table.WETB_MIN_QUAL,obs_table.DWPT_MAX,obs_table.DWPT_MAX_QUAL,obs_table.DWPT_MIN,obs_table.DWPT_MIN_QUAL,obs_table.REL_HUM,obs_table.REL_HUM_QUAL,obs_table.REL_HUM_MAX,obs_table.REL_HUM_MAX_QUAL,obs_table.REL_HUM_MIN,obs_table.REL_HUM_MIN_QUAL,obs_table.STN_PRES,obs_table.STN_PRES_QUAL,obs_table.MSL_PRES,obs_table.MSL_PRES_QUAL,obs_table.QNH,obs_table.QNH_QUAL,obs_table.VSBY,obs_table.VSBY_QUAL,obs_table.VSBY_10,obs_table.VSBY_10_QUAL,obs_table.CUM_PRCP,obs_table.PRCP,obs_table.PRCP_QUAL,obs_table.PRCP_PER,obs_table.CUM_WND_RUN,obs_table.WND_RUN,obs_table.WND_RUN_QUAL,obs_table.WND_RUN_PER,obs_table.CUM_SUN_SEC,obs_table.SUN_SEC,obs_table.SUN_SEC_QUAL,obs_table.SUN_PER,obs_table.CUM_LTNG_CNT,obs_table.LTNG_CNT,obs_table.LTNG_CNT_QUAL,obs_table.LTNG_PER,obs_table.CLD_HT_1,obs_table.CLD_HT_1_QUAL,obs_table.CLD_HT_2,obs_table.CLD_HT_2_QUAL,obs_table.CLD_HT_3,obs_table.CLD_HT_3_QUAL,obs_table.CLD_HT_4,obs_table.CLD_HT_4_QUAL,obs_table.CLD_HT_5,obs_table.CLD_HT_5_QUAL,obs_table.CLD30_AMT_1,obs_table.CLD30_AMT_1_QUAL,obs_table.CLD30_HT_1,obs_table.CLD30_HT_1_QUAL,obs_table.CLD30_AMT_2,obs_table.CLD30_AMT_2_QUAL,obs_table.CLD30_HT_2,obs_table.CLD30_HT_2_QUAL,obs_table.CLD30_AMT_3,obs_table.CLD30_AMT_3_QUAL,obs_table.CLD30_HT_3,obs_table.CLD30_HT_3_QUAL,obs_table.SOIL_5_TEMP,obs_table.SOIL_5_TEMP_QUAL,obs_table.SOIL_10_TEMP,obs_table.SOIL_10_TEMP_QUAL,obs_table.SOIL_20_TEMP,obs_table.SOIL_20_TEMP_QUAL,obs_table.SOIL_50_TEMP,obs_table.SOIL_50_TEMP_QUAL,obs_table.SOIL_100_TEMP,obs_table.SOIL_100_TEMP_QUAL,obs_table.TERR_TEMP,obs_table.TERR_TEMP_QUAL,obs_table.WTR_TEMP,obs_table.WTR_TEMP_QUAL,obs_table.INT_TEMP,obs_table.INT_TEMP_QUAL,obs_table.BAT_VOLT,obs_table.BAT_VOLT_QUAL,obs_table.CMT

/// Want to resample data in 10 min intervals, starting at UTC00:00, grouped by station
/// Data fields should use avg() to aggregate, other fields should use the first entry in order
/// of time
///
/// Station number:
/// - STN_NUM
///
/// Time fields:
/// - LSD, DATE_CREATED, LAST_UPDATE, TM, LCT, CMT
/// > NOTE: TM is utc time
///
/// Quality fields:
/// - ends_with("QUAL")
///
/// somewhat similar to:
///
/// ```
/// df.sql(
///     "SELECT \
///      date_bin('10 minutes', \"TM\", TIMESTAMP '1900-01-01T00:00:00') as tm_bin, \
///      \"STN_NUM\", AVG(*) \
///      FROM obs_table \
///      GROUP BY \"STN_NUM\", tm_bin \
///      SORT tm_bin, \"STN_NUM\""
/// );
/// ```
/// except AVG(*) won't normally work with pure SQL since there's no easy way to ommit columns
/// and there are too many columns to list
async fn resample_to_10_min(ctx: &SessionContext) -> datafusion::error::Result<()> {
    // ----
    // get table columns from context
    //
    // NOTE: this is trying to be unnecessarily smart, but can be declared manually
    // if needed given the database is unlikely to change
    let df = ctx.table("obs_table").await?;

    // ----
    // extract columns that contain values
    let cols = df.schema().field_names();
    let time_fields = [
        r#"LSD"#,
        r#"DATE_CREATED"#,
        r#"LAST_UPDATE"#,
        r#"TM"#,
        r#"LCT"#,
        r#"CMT"#,
    ];
    let stn_col = r#"STN_NUM"#;
    let time_col = r#"TM"#;
    let time_col_bin = r#"TM_BIN"#;
    let value_cols = cols
        .iter()
        .map(|x| x.split(".").last().unwrap())
        .filter(|x| !(x.ends_with(r#"QUAL"#) || time_fields.contains(x) || x.eq(&stn_col)))
        .collect::<Vec<&str>>();
    // ----

    // ----
    // columns to keep
    let mut keep_cols = value_cols.clone();
    keep_cols.append(vec![stn_col, time_col, time_col_bin].as_mut());
    // ----

    println!("{:?}", keep_cols);
    println!("{:?}", value_cols);

    let df = df
        .with_column(
            time_col_bin,
            call_fn(
                "date_bin",
                vec![
                    lit("10 minutes"),
                    ident(time_col),
                    lit("1900-01-01T00:00:00"),
                ],
            )
            .unwrap(),
        )?
        .select_columns(&keep_cols)?
        .aggregate(
            vec![ident(time_col_bin), ident(stn_col)],
            value_cols.iter().map(|&x| avg(ident(x))).collect(),
        )?
        .sort(vec![
            ident(time_col_bin).sort(true, false),
            ident(stn_col).sort(true, false),
        ])?;

    // ----
    // For testing only:
    //
    // Spit out plan to make sure we're doing the right thing
    println!("{:?}", df.logical_plan());

    // write to csv so its examinable
    df.write_csv(
        "/home/nvr90/tmp/test_data_fusion_10_min_resample_query.csv",
        DataFrameWriteOptions::default().with_single_file_output(true),
        None,
    )
    .await?;

    Ok(())
    // ---
}

fn extract_files_year_month(
    tar_path: &Path,
    dst_dir: &Path,
    year: u32,
    month: u32,
) -> Result<(), std::io::Error> {
    // stores input files into intermediate directories before attempting to combine and resample
    assert!(month <= 12);

    println!(
        "processing input: {} to output: {}",
        // this "consumes" tar_path - try without arc?
        // => returns a new "Option" type with a reference to &str
        // => when unwrap happens, Option is discarded, but &str is retrieved - which is still a
        // reference so tar_path still lives on
        tar_path.to_str().unwrap(),
        dst_dir.to_str().unwrap()
    );

    let mut ta = Archive::new(File::open(tar_path)?);
    let _ = ta
        .entries()? // return entries by value => consumption
        .filter_map(|x| x.ok())
        .map(move |mut x| -> Result<PathBuf, std::io::Error> {
            // should be able to consume here so can probably use move
            // |mut x| => borrow and force it to be mutable
            // only extract files for the given year-month
            //.(format!("{}-{:0>2}", year, month).cloned())
            let path = x.path()?; // no cloning required here - just need the path
            if path.extension().unwrap() == "pq"
                && path
                    .to_str()
                    .unwrap()
                    .contains(format!("{}-{:0>2}", year, month).as_str())
            {
                let dst_path = dst_dir.to_owned().join(path.file_name().unwrap());
                x.unpack(&dst_path)?;
                return Ok(dst_path);
            }

            Err(std::io::Error::new(
                std::io::ErrorKind::NotFound,
                "no valid files found in tarball",
            ))
        })
        .filter_map(|x| x.ok())
        .for_each(|x| println!("> {}", x.display()));
    Ok(())
}

fn main() {
    // uses reference counter => safe to clone
    let tar_path = Arc::new(Path::new(
        "/home/nvr90/repos/data_engineering/projects/combine_parquet/combpq/blah2020.tar",
    ));

    // uses reference counter => safe to clone
    let dest_path = Arc::new(Path::new(
        "/home/nvr90/repos/data_engineering/projects/combine_parquet/combpq/dst",
    ));

    let year: u32 = 2022;
    let month: u32 = 4;
    // integers are not stored as pointers so pass directly
    // tar and dest path sent through as reference
    let dst_dir = dest_path.to_owned().join(format!("{}-{:0>2}", year, month)); // require clone as we don't want
                                                                                // to change teh underlying path
    DirBuilder::new()
        .recursive(true)
        .create(&dst_dir)
        .expect(format!("Could not create directory: {}", dst_dir.display()).as_str());

    //    println!("extracting tar archive: {}", tar_path.display());
    //    extract_files_year_month(&tar_path, &dst_dir, year, month).expect("Could not untar files.");
    println!("Attempting to resample data from: {}", dst_dir.display());
    resample_parquet_data(&dst_dir).expect("Could not resample");
}

// --- Tests ---

// -------------------------------------------------------------------------------------------------
// Useless (fun?) experimentation
// -------------------------------------------------------------------------------------------------
// Number of threads to workflow on
const _NUM_THREADS: u32 = 8;
// number of files per thread - this entirely depends on the size of each file and may need to be
// tweaked
const _BATCH_SIZE: u32 = 30;
// we have 1 min samples, we want to down sample to 10min aggregation
const TEN_MIN_SAMPLES: usize = 10;

#[inline]
#[allow(dead_code)]
fn compute_mean(a: [f64; TEN_MIN_SAMPLES], n: Option<usize>) -> f64 {
    a.iter().sum::<f64>() / (n.unwrap_or(TEN_MIN_SAMPLES) as f64)
}

#[allow(dead_code)]
fn iterate_by_five_and_mean(x: &Vec<f64>) -> Vec<f64> {
    // Takes elements from a batch size of 5 repeatedly from the input vector and performs a mean
    // calculation.
    let mut iter = x.clone().into_iter();
    std::iter::repeat(5_usize)
        .map(|n| {
            let mut items = iter.by_ref().take(n).collect::<Vec<f64>>();
            match items.len() {
                0 => f64::NAN,
                _ => {
                    let mut items_arr = [0.0_f64; TEN_MIN_SAMPLES];
                    items_arr[0..items.len()].swap_with_slice(&mut items);
                    compute_mean(items_arr, Some(items.len()))
                }
            }
        })
        .take_while(|n| !n.is_nan())
        .collect::<Vec<f64>>()
}

// --- Tests ---

#[test]
fn test_compute_mean() {
    let mut a: [f64; TEN_MIN_SAMPLES] = [1.0; TEN_MIN_SAMPLES];
    assert_eq!(compute_mean(a, None), 1.0);
    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0];
    assert_eq!(compute_mean(a, None), 5.5);
}

#[test]
fn test_iterate_by_five_and_mean() {
    let a: Vec<f64> = (0..97).map(|x| x as f64).collect();
    assert_eq!(
        *iterate_by_five_and_mean(&a).last().unwrap(),
        ((94 + 95 + 96 + 97) as f64) / 4.0
    );
}
