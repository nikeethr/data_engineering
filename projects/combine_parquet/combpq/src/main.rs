// Number of threads to workflow on
const NUM_THREADS: u32 = 8;
// number of files per thread - this entirely depends on the size of each file and may need to be
// tweaked
const BATCH_SIZE: u32 = 30;
// we have 1 min samples, we want to down sample to 10min aggregation
const SAMPLES_PER_HOUR: usize = 10; 

fn compute_mean(a: &[f64; SAMPLES_PER_HOUR], n: Option<usize>) -> f64 {
    a.iter().sum::<f64>() / (n.unwrap_or(SAMPLES_PER_HOUR) as f64)
}

fn main() {
    let a: [f64; SAMPLES_PER_HOUR] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0];
    println!("{}", compute_mean(&a, None));
}


#[test]
fn test_compute_mean() {
    let mut a: [f64; SAMPLES_PER_HOUR] = [1.0; SAMPLES_PER_HOUR];
    assert_eq!(compute_mean(&a, None), 1.0);
    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0];
    assert_eq!(compute_mean(&a, None), 5.5);
}
