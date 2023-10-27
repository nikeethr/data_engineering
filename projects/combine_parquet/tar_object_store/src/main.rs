use crate::tar_metadata::{AdamTarMetadataExtract};
use crate::tar_object_store::AdamTarFileObjectStore;




use std::io::Write;



pub(crate) mod resampler;
pub(crate) mod tar_metadata;
pub(crate) mod tar_object_store;

// NOTE: this can only work for small-ish archives, if we have >100,000 in the archive files for
// example this can use up a lot of memory, and may be better to process in batches.
//
// extract_tar_entry_file_metadata -> Vec<EntryMetadata>
// iter.for_each filename in metadata ->

fn main() {
    // TODO: clean this up into command line args
    // NOTE: these are file date ranges, and do not necessarily correspond to the actual obs date.
    // As such it may be better to index the entire tar_file.
    // TODO: add option to index entire tar file and cache it.
    let locations =
        AdamTarMetadataExtract::construct_locations_from_date_range("2022-04-01", "2022-04-05");

    let tar_path =
        "/home/nvr90/repos/data_engineering/projects/combine_parquet/combpq/blah2020.tar"
            .to_string();

    let prefix = "nowboost/tjl/one_minute_data".to_string();

    let adam_tar_store = AdamTarFileObjectStore::new_with_locations(locations, &tar_path, &prefix);

    std::io::stdout().flush().unwrap();

    let adam_resampler = resampler::ParquetResampler::new(
        adam_tar_store,
        resampler::DataFreq::OneMin,
        resampler::DataFreq::OneHour,
        resampler::FilePartition::ByStation,
        Some(r#"LSD"#.to_string()),
        Some(r#"STN_NUM"#.to_string()),
        Some(vec![
            r#"AIR_TEMP"#.to_string(),
            r#"AIR_TEMP_MIN"#.to_string(),
            r#"AIR_TEMP_MAX"#.to_string(),
            r#"DWPT"#.to_string(),
        ]),
    );

    resampler::ParquetResampler::resample(adam_resampler.clone()).unwrap();
}

// TODO: CLI
// CLI:
// use clap::{Arg, App};

// fn main() {
//     let matches = App::new("My Test Program")
//         .version("0.1.0")
//         .author("Hackerman Jones <hckrmnjones@hack.gov>")
//         .about("Teaches argument parsing")
//         .arg(Arg::with_name("file")
//                  .short("f")
//                  .long("file")
//                  .takes_value(true)
//                  .help("A cool file"))
//         .arg(Arg::with_name("num")
//                  .short("n")
//                  .long("number")
//                  .takes_value(true)
//                  .help("Five less than your favorite number"))
//         .get_matches();
//
//     let myfile = matches.value_of("file").unwrap_or("input.txt");
//     println!("The file passed is: {}", myfile);
//
//     let num_str = matches.value_of("num");
//     match num_str {
//         None => println!("No idea what your favorite number is."),
//         Some(s) => {
//             match s.parse::<i32>() {
//                 Ok(n) => println!("Your favorite number must be {}.", n + 5),
//                 Err(_) => println!("That's not a number! {}", s),
//             }
//         }
//     }
// }
