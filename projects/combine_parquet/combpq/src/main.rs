// --- Actual implementation ---

// --- Useless (fun?) experimentation ---
// Number of threads to workflow on
const _NUM_THREADS: u32 = 8;
// number of files per thread - this entirely depends on the size of each file and may need to be
// tweaked
const _BATCH_SIZE: u32 = 30;
// we have 1 min samples, we want to down sample to 10min aggregation
const TEN_MIN_SAMPLES: usize = 10;

fn compute_mean(a: [f64; TEN_MIN_SAMPLES], n: Option<usize>) -> f64 {
    a.iter().sum::<f64>() / (n.unwrap_or(TEN_MIN_SAMPLES) as f64)
}

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

fn main() {
    let a: [f64; TEN_MIN_SAMPLES] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0];
    println!("{}", compute_mean(a, None));

    let a2: Vec<f64> = (0..103).map(|x| x as f64).collect();
    println!("{:?}", iterate_by_five_and_mean(&a2));
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
