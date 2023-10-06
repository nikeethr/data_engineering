// use datafusion::prelude::*;
use std::fs::{DirBuilder, File};
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tar::Archive;

// -------------------------------------------------------------------------------------------------
// Actual implementation
// -------------------------------------------------------------------------------------------------
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
        tar_path.to_str().unwrap(),
        dst_dir.to_str().unwrap()
    );

    let mut ta = Archive::new(File::open(tar_path).unwrap());
    let _ = ta
        .entries()?
        .filter_map(|x| x.ok())
        .map(|mut x| -> Result<PathBuf, std::io::Error> {
            // |mut x| => borrow and force it to be mutable
            // only extract files for the given year-month
            let path = x.path()?.to_owned();
            let f_pre = format!("{}-{:0>2}", year, month);
            let dst_dir_month = dst_dir.to_owned().join(&f_pre);
            DirBuilder::new().recursive(true).create(&dst_dir_month)?;

            if path.extension().unwrap() == "pq" && path.to_str().unwrap().contains(&f_pre) {
                let dst_path = dst_dir_month.to_owned().join(path.file_name().unwrap());
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
    let tar_path = Arc::new(Path::new(
        "/home/nvr90/repos/data_engineering/projects/combine_parquet/combpq/blah2020.tar",
    ));
    let dest_path = Arc::new(Path::new(
        "/home/nvr90/repos/data_engineering/projects/combine_parquet/combpq/dst",
    ));

    let year: u32 = 2022;
    let month: u32 = 4;
    let _ = extract_files_year_month(&tar_path, &dest_path, year, month);
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
