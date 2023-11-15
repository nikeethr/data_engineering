use nalgebra::ComplexField;
use rayon::prelude::*;
use std::sync::{Arc, Mutex};

/// calculate the histogram of a 1-D array given the number of bins
/// this is overly simplistic and will not work well for sparse intervals
pub fn hist_1d(a: &Vec<f64>, bins: u64) -> Vec<(f64, f64, u64)> {
    let a_max = a
        .clone()
        .into_iter()
        .filter(|x| !x.is_nan())
        .reduce(f64::max)
        .unwrap();

    let a_min = a
        .clone()
        .into_iter()
        .filter(|x| !x.is_nan())
        .reduce(f64::min)
        .unwrap();
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
            if !a[j].is_nan() && a[j] > start && a[j] < stop {
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
    let n = a.iter().filter(|x| !x.is_nan()).count();
    assert!(n > 3);
    let n_f = n as f64;

    // moments
    let x_mu: f64 = a.iter().filter(|x| !x.is_nan()).sum::<f64>() / n_f;
    let m_3 = Mutex::new(0.0);
    let s_3 = Mutex::new(0.0);
    let a = Arc::new(a);

    unsafe {
        (0..n).into_par_iter().for_each(|i| {
            let x = a.get_unchecked(i);
            if !x.is_nan() {
                let mut m_3_ = m_3.lock().unwrap();
                *m_3_ += (x - x_mu).powi(3);
                let mut s_3_ = s_3.lock().unwrap();
                *s_3_ += (x - x_mu).powi(2);
            }
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
    let n = a.iter().filter(|x| !x.is_nan()).count();
    assert!(n > 3);
    let n_f = n as f64;

    // moments
    let x_mu: f64 = a.iter().filter(|x| !x.is_nan()).sum::<f64>() / n_f;
    let m_4 = Mutex::new(0.0);
    let m_22 = Mutex::new(0.0);
    let a = Arc::new(a);

    unsafe {
        (0..n).into_par_iter().for_each(|i| {
            let x = a.get_unchecked(i);
            if !x.is_nan() {
                let mut m_4_ = m_4.lock().unwrap();
                *m_4_ += (x - x_mu).powi(4);
                let mut m_22_ = m_22.lock().unwrap();
                *m_22_ += (x - x_mu).powi(2);
            }
        });
    }

    let m_4 = m_4.into_inner().unwrap() / n_f;
    let m_22 = (m_22.into_inner().unwrap() / n_f).powi(2);

    approx::assert_relative_ne!(m_22, 0.0);
    m_4 / m_22 - 3.0
}

/// yeo-johnson is a special case of box-cox, with only 1 parameter to optimize and hence is
/// easier to optimize.
/// reference: https://en.wikipedia.org/wiki/Power_transform
///
/// Methodology
/// -----------
/// we know that lambda is roughly between -5 -> 5, with -5 and 5 being extreme corrections which
/// are unlikely to be used. therefore, we can strategise the optimization by the
///
/// ideally, we can use something like Chi-squared test to score the goodness of fit. But for now
/// we use the available skewness and kurtosis metrics to determine lambda that optimizes each one.
///
/// ideally the optimal lambda is quite similar for both kurtosis & skew. Though we're more
/// interested in correcting for skew.
///
/// returns optimal lambda in the following format ((skew, lambda), (kurtosis, lambda))
pub fn yeo_johnson_1d_power_correction(a: &Vec<f64>) -> ((f64, f64), (f64, f64)) {
    // identity: lambda = 1, therefore the hyperparameters should centre around 1 and spread out
    // monotonically increasing in steps
    // Array[(steps, cutoff)]
    let lambda_ref: f64 = 1.0;
    let lambda_pos = binned_spread(vec![(100, 0.5), (30, 1.0), (10, 3.0)], lambda_ref);
    let lambda_neg = binned_spread(vec![(100, -0.5), (30, -1.0), (10, -3.0)], lambda_ref);
    let lambdas = lambda_pos
        .into_iter()
        .chain(vec![lambda_ref].into_iter())
        .chain(lambda_neg.into_iter());
    let scores = Arc::new(Mutex::new(Vec::new()));
    let a = Arc::new(a);

    lambdas.par_bridge().for_each(|l| {
        let a_pow = yeo_johnson_1d(a.clone(), l);
        let k = kurtosis_1d(&a_pow);
        let s = skewness_1d(&a_pow);
        scores.lock().unwrap().push((k, s, l));
    });

    let scores = Arc::into_inner(scores).unwrap().into_inner().unwrap();
    macro_rules! best_score {
        ($i:literal) => {
            scores.iter().fold((f64::INFINITY, f64::NAN), |acc, x| {
                let cmp_x = match $i {
                    0 => x.0,
                    1 => x.1,
                    _ => unreachable!(),
                };
                if acc.0 < f64::abs(cmp_x) {
                    acc
                } else {
                    (cmp_x, x.2)
                }
            })
        };
    }
    let least_kurtosis = best_score!(0);
    let least_skew = best_score!(1);
    (least_skew, least_kurtosis)
}

/// Takes in a vector of spread_tiers = (n_bins, cutoff), and a starting point, where parameters
/// values are uniformly spread in (cutoff[i] - cutoff[i-1]) / n_bins[i] intervals between any two
/// cutoffs. See tests for examples.
fn binned_spread(spread_tiers: Vec<(u64, f64)>, start: f64) -> Vec<f64> {
    spread_tiers.iter().fold(vec![start], |mut acc, x| {
        let prev_cutoff = acc.last().cloned().unwrap();
        acc.extend(
            (1..(x.0 + 1)).map(|i| prev_cutoff + (i as f64) * (x.1 - prev_cutoff) / x.0 as f64),
        );
        acc
    })
}

pub fn yeo_johnson_1d(a: Arc<&Vec<f64>>, lambda: f64) -> Vec<f64> {
    (0..a.len())
        .into_par_iter()
        .map(|i| unsafe {
            let x = a.get_unchecked(i);
            if !x.is_nan() {
                yeo_johnson_scalar(*x, lambda)
            } else {
                f64::NAN
            }
        })
        .collect::<Vec<_>>()
}

fn yeo_johnson_scalar(sample: f64, lambda: f64) -> f64 {
    let x = sample;
    let l = lambda;
    if x >= 0.0 {
        if approx::relative_eq!(l, 0.0) {
            f64::ln(x + 1.0)
        } else {
            ((x + 1.0).powf(l) - 1.0) / l
        }
    } else {
        // x < 0
        if approx::relative_eq!(l, 2.0) {
            -f64::ln(-x + 1.0)
        } else {
            -((-x + 1.0).powf(2.0 - l) - 1.0) / (2.0 - l)
        }
    }
}

pub fn yeo_johnson_inv_1d(a: Arc<&Vec<f64>>, lambda: f64) -> Vec<f64> {
    (0..a.len())
        .into_par_iter()
        .map(|i| unsafe {
            let x = a.get_unchecked(i);
            if !x.is_nan() {
                yeo_johnson_scalar_inv(*x, lambda)
            } else {
                f64::NAN
            }
        })
        .collect::<Vec<_>>()
}

fn yeo_johnson_scalar_inv(sample: f64, lambda: f64) -> f64 {
    let x = sample;
    let l = lambda;
    if x >= 0.0 {
        if approx::relative_eq!(l, 0.0) {
            x.exp() - 1.0
        } else {
            (x * l + 1.0).powf(1.0 / l) - 1.0
        }
    } else {
        // x < 0
        if approx::relative_eq!(l, 2.0) {
            -((-x).exp() - 1.0)
        } else {
            -((-x * (2.0 - l) + 1.0).powf(1.0 / (2.0 - l)) - 1.0)
        }
    }
}

#[test]
fn test_yeo_johnson_scalar_identity() {
    let res = yeo_johnson_scalar(5.0, 1.0);
    println!("yj={:?}", res);
    assert_relative_eq!(5.0, res);
}

#[test]
fn test_yeo_johnson_scalar_boundaries() {
    let boundaries = vec![
        (5.0, 0.0),
        (-5.0, 2.0),
        (-5.0, 2.0),
        (-5.0, 0.0),
        (0.0, -2.0),
    ];
    for (sample, lambda) in boundaries {
        let res = yeo_johnson_scalar(sample, lambda);
        println!("yj={:?}", res);
    }
}

#[test]
fn test_yeo_johnson_scalar_inv_identity() {
    let boundaries = vec![
        (5.0, 0.0),
        (-5.0, 2.0),
        (-5.0, 2.0),
        (-5.0, 0.0),
        (0.0, -2.0),
        (9.0, -1.5),
        (5.0, 1.5),
        (-5.0, 1.5),
        (-9.0, -1.5),
    ];
    for (sample, lambda) in boundaries {
        let res = yeo_johnson_scalar_inv(yeo_johnson_scalar(sample, lambda), lambda);
        println!("yj={:?}", res);
    }
}

#[test]
fn test_binned_spread() {
    let x_ref = 1.0;
    let x_pos = binned_spread(vec![(100, 1.5), (30, 3.0), (10, 4.0)], x_ref);
    let x_neg = binned_spread(vec![(100, 0.5), (30, -1.0), (10, -3.0)], x_ref);
    let mut xs = x_pos
        .into_iter()
        .chain(x_neg.into_iter())
        .collect::<Vec<_>>();
    xs.sort_unstable_by(|a, b| a.partial_cmp(b).unwrap());
    println!("xs={:?}", xs);
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
    approx::assert_relative_eq!(res, 0.917961610478289, epsilon = (f64::EPSILON * 100.0));
}

#[test]
fn test_no_skew() {
    let a = vec![
        9.0, 8.0, 8.0, 7.0, 7.0, 7.0, 6.0, 6.0, 6.0, 6.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0,
        5.0, 4.0, 4.0, 4.0, 4.0, 3.0, 3.0, 3.0, 2.0, 2.0, 1.0,
    ];
    let res = skewness_1d(&a);
    println!("{:?}", res);
    approx::assert_relative_eq!(res, 0.0, epsilon = (f64::EPSILON * 100.0));
}

#[test]
fn test_kurtosis_narrow() {
    let a = vec![0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 0.5, 0.0, 0.0, 0.0, 0.0];
    let res = kurtosis_1d(&a);
    println!("{:?}", res);
    approx::assert_relative_eq!(res, 1.0664000000000016, epsilon = (f64::EPSILON * 100.0));
}

#[test]
fn test_kurtosis_wide() {
    let a = vec![
        1.0, 1.0, 0.9, 0.9, 0.9, 0.8, 0.8, 0.8, 0.8, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7,
    ];
    let res = kurtosis_1d(&a);
    println!("{:?}", res);
    approx::assert_relative_eq!(res, -1.012865025730047, epsilon = (f64::EPSILON * 100.0));
}

#[test]
fn test_kurtosis_normal() {
    let a = vec![
        9.0, 8.0, 8.0, 7.0, 7.0, 7.0, 6.0, 6.0, 6.0, 6.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0,
        5.0, 4.0, 4.0, 4.0, 4.0, 3.0, 3.0, 3.0, 2.0, 2.0, 1.0,
    ];
    let res = kurtosis_1d(&a);
    println!("{:?}", res);
    approx::assert_relative_eq!(res, -0.273999999999999, epsilon = (f64::EPSILON * 100.0));
}

// ------------------------------------------------------------------------------------------------
// TODO: implement boxcox
// lambda and alpha
// pub type BoxCoxParams = (f64, f64);

// Determine power law to use to force the normal distribution uses profile likelihood to determine
// parameters lambda and alpha requires that the sample size be relatively large. Or may spit out
// weird results.
// reference: https://en.wikipedia.org/wiki/Power_transform
// pub fn optimize_box_cox_1d(a: &Vec<f64>) -> BoxCoxParams {
// split samples into two

// (0.0, 0.0)
// }

// pub fn box_cox_1d(p: BoxCoxParams) -> {

// }

// fn box_cox_1d_derv_alpha() -> {
// Alg
// ---
// sample N/2 values from population without replacement. Where N is the population size.
// let alpha arbitrarily = min(0, x_1), where alpha = constant shift parameter and x_1 = N/2 obs
// call the arbitrary alpha above alpha_.
// let f(x; alpha, lambda) = box_cox_1d transform.
// assume alpha(lambda) i.e. alpha is a function of lambda.
//
// model the following:
//     - alpha using x_1, and [1]
//     - lambda using x_2 (the remaining N/2 samples) with alpha assumed to be constant [2]
// i.e. [1] => f(x_1; alpha(lambda); lambda) = ((x_1_i + a)^l - 1) / l,  for all x_1_i in x_1
//      [2] => f(x_2; alpha_; lambda) = ((x_2_i + a_)^l - 1) / l, for all x_2_i in x_2
// subtract [2] or f2 from [1] or f1 and find lambda that maximizes this difference.
//
// arbitrarily we do this heuristically using

// }
// ------------------------------------------------------------------------------------------------
