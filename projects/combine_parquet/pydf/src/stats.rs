use rayon::prelude::*;
use std::sync::{Arc, Mutex};

/// calculate the histogram of a 1-D array given the number of bins
/// this is overly simplistic and will not work well for sparse intervals
pub fn hist_1d(a: &Vec<f64>, bins: u64) -> Vec<(f64, f64, u64)> {
    let a_max = a.clone().into_iter().reduce(f64::max).unwrap();
    let a_min = a.clone().into_iter().reduce(f64::min).unwrap();
    let interval = (a_max - a_min) / (bins as f64);

    let start = a_min;
    let stop = a_min + interval;

    let intervals = (0..bins)
        .map(|n| -> (f64, f64, u64) {
            (
                start + (n as f64) * interval,
                stop + (n as f64) * interval,
                n,
            )
        })
        .collect::<Vec<_>>();

    let hist = Arc::new(Mutex::new(vec![(0.0, 0.0, 0); bins as usize]));

    intervals.into_par_iter().for_each(|(start, stop, n)| {
        let mut count: u64 = 0;
        for j in 0..a.len() {
            if a[j] > start && a[j] < stop {
                count += 1;
            }
        }
        let hist_ = hist.lock().unwrap().as_mut_ptr();
        unsafe {
            let x = hist_.add(n as usize);
            *x = (start, stop, count);
        }
    });

    Arc::into_inner(hist).unwrap().into_inner().unwrap()
}

/// fisher's moment coefficient of skewness, we use a simple method of natural biased estimator
/// reference: https://en.wikipedia.org/wiki/Skewness#Sample_skewness, see equation for b1
pub fn skewness_1d(a: &Vec<f64>) -> f64 {
    assert!(a.len() > 3);

    let n = a.len();
    let n_f = n as f64;
    // mean
    let x_mu: f64 = a.iter().sum::<f64>() / n_f;
    let m_3 = Mutex::new(0.0);
    let s_3 = Mutex::new(0.0);
    let a = Mutex::new(Arc::new(a));

    unsafe {
        (0..n).into_par_iter().for_each(|i| {
            let ptr = a.lock().unwrap().as_ptr();
            let x = ptr.add(i);
            let mut m_3_ = m_3.lock().unwrap();
            let mut s_3_ = s_3.lock().unwrap();
            *m_3_ += (*x - x_mu).powi(3);
            *s_3_ += (*x - x_mu).powi(2);
        });
    }

    let m_3 = m_3.into_inner().unwrap() / n_f;
    let s_3 = (s_3.into_inner().unwrap() / (n_f - 1.0)).powf(1.5);

    approx::assert_relative_ne!(s_3, 0.0);
    m_3 / s_3
}

/// Sample kurtosis metho of moments natural biased estimator
/// reference: https://en.wikipedia.org/wiki/Kurtosis#A_natural_but_biased_estimator
/// see equation for g2
pub fn kurtosis_1d(a: &Vec<f64>) -> f64 {
    assert!(a.len() > 3);

    let n = a.len();
    let n_f = n as f64;
    // mean
    let x_mu: f64 = a.iter().sum::<f64>() / n_f;
    let m_4 = Mutex::new(0.0);
    let m_22 = Mutex::new(0.0);
    let a = Mutex::new(Arc::new(a));

    unsafe {
        (0..n).into_par_iter().for_each(|i| {
            let ptr = a.lock().unwrap().as_ptr();
            let x = ptr.add(i);
            let mut m_4_ = m_4.lock().unwrap();
            let mut m_22_ = m_22.lock().unwrap();
            *m_4_ += (*x - x_mu).powi(4);
            *m_22_ += (*x - x_mu).powi(2);
        });
    }

    let m_4 = m_4.into_inner().unwrap() / n_f;
    let m_22 = (m_22.into_inner().unwrap() / n_f).powi(2);

    approx::assert_relative_ne!(m_22, 0.0);
    m_4 / m_22 - 3.0
}

#[test]
fn test_hist_1d() {
    let a = vec![
        1.0, 1.0, 1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 3.0, 3.0, 5.0, 5.0, 5.0, 1.0, 1.0, 1.0, 2.0, 2.0,
        6.0, 6.0, 6.0, 6.0, 3.0, 4.0, 15.0,
    ];
    let res = hist_1d(&a, 6);
    let exp = [
        (1.0, 3.3333333333333335, 8),
        (3.3333333333333335, 5.666666666666667, 4),
        (5.666666666666667, 8.0, 4),
        (8.0, 10.333333333333334, 0),
        (10.333333333333334, 12.666666666666668, 0),
        (12.666666666666668, 15.000000000000002, 1),
    ];
    println!("{:?}", res);
    for i in 0..res.len() {
        approx::assert_relative_eq!(res.iter().nth(i).unwrap().0, exp.iter().nth(i).unwrap().0);
        approx::assert_relative_eq!(res.iter().nth(i).unwrap().1, exp.iter().nth(i).unwrap().1);
        assert_eq!(res.iter().nth(i).unwrap().2, exp.iter().nth(i).unwrap().2);
    }
}

#[test]
fn test_skewed() {
    let a = vec![
        6.0, 5.0, 5.0, 4.0, 4.0, 4.0, 3.0, 3.0, 3.0, 2.0, 2.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 1.0,
        1.0, 1.0, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
    ];
    let res = skewness_1d(&a);
    println!("{:?}", res);
    approx::assert_relative_eq!(res, 0.9179616104782891);
}

#[test]
fn test_no_skew() {
    let a = vec![
        9.0, 8.0, 8.0, 7.0, 7.0, 7.0, 6.0, 6.0, 6.0, 6.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0,
        5.0, 4.0, 4.0, 4.0, 4.0, 3.0, 3.0, 3.0, 2.0, 2.0, 1.0,
    ];
    let res = skewness_1d(&a);
    println!("{:?}", res);
    approx::assert_relative_eq!(res, 0.0);
}

#[test]
fn test_kurtosis_narrow() {
    let a = vec![0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0];
    let res = kurtosis_1d(&a);
    println!("{:?}", res);
    // approx::assert_relative_eq!(res, 0.9179616104782891);
}

#[test]
fn test_kurtosis_wide() {
    let a = vec![
        1.0, 1.0, 0.9, 0.9, 0.9, 0.8, 0.8, 0.8, 0.8, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7,
    ];
    let res = kurtosis_1d(&a);
    println!("{:?}", res);
    // approx::assert_relative_eq!(res, 0.9179616104782891);
}

#[test]
fn test_kurtosis_normal() {
    let a = vec![
        9.0, 8.0, 8.0, 7.0, 7.0, 7.0, 6.0, 6.0, 6.0, 6.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0,
        5.0, 4.0, 4.0, 4.0, 4.0, 3.0, 3.0, 3.0, 2.0, 2.0, 1.0,
    ];
    let res = kurtosis_1d(&a);
    println!("{:?}", res);
    // approx::assert_relative_eq!(res, 0.0);
}
