use object_store::ObjectStore;

pub(crate) mod tar_metadata;
pub(crate) mod tar_object_store;
use crate::tar_metadata::{print_adam_metadata_stats, AdamTarMetadataExtract};
use crate::tar_object_store::AdamTarFileObjectStore;
use datafusion::arrow::datatypes::DataType;
use datafusion::datasource::{
    file_format::parquet::ParquetFormat,
    listing::{ListingOptions, ListingTableInsertMode},
};
use datafusion::prelude::*;
use futures::prelude::*;
use std::sync::Arc;
use url::Url;

// NOTE: this can only work for small-ish archives, if we have >100,000 in the archive files for
// example this can use up a lot of memory, and may be better to process in batches.
//
// extract_tar_entry_file_metadata -> Vec<EntryMetadata>
// iter.for_each filename in metadata ->
//
//
//

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

fn main() {
    // TODO: clean this up into command line args
    let locations =
        AdamTarMetadataExtract::construct_locations_from_date_range("2022-04-01", "2022-04-05");

    let tar_path =
        "/home/nvr90/repos/data_engineering/projects/combine_parquet/combpq/blah2020.tar"
            .to_string();

    let prefix = "nowboost/tjl/one_minute_data".to_string();

    let adam_tar_store = AdamTarFileObjectStore::new_with_locations(locations, &tar_path, &prefix);

    print_adam_metadata_stats(&adam_tar_store.tar_metadata_all);

    {
        #[tokio::main(flavor = "multi_thread")]
        async fn inner(adam_tar_store: Arc<AdamTarFileObjectStore>) -> tokio::io::Result<()> {
            tokio::spawn(async move {
                let x = adam_tar_store.list(None).await.unwrap();
                println!("{:?}", x.collect::<Vec<_>>().await);

                // TODO: below should be extracted into modules
                let ctx = SessionContext::new();
                ctx.runtime_env().register_object_store(
                    &Url::parse(tar_object_store::TAR_PQ_STORE_BASE_URI).unwrap(),
                    adam_tar_store,
                );

                ctx.register_listing_table(
                    "adam_obs",
                    tar_object_store::TAR_PQ_STORE_BASE_URI,
                    ListingOptions::new(Arc::new(ParquetFormat::default()))
                        .with_file_extension(".parquet")
                        .with_table_partition_cols(vec![("date".to_string(), DataType::Date32)])
                        .with_file_sort_order(vec![vec![col("date").sort(true, true)]])
                        .with_insert_mode(ListingTableInsertMode::Error),
                    None,
                    None,
                )
                .await
                .unwrap();

                ctx.table("adam_obs")
                    .await
                    .unwrap()
                    .filter(col("date").gt_eq(lit("2022-04-04")))
                    .unwrap()
                    .show_limit(10)
                    .await
                    .unwrap();
            })
            .await?;
            Ok(())
        }
        inner(adam_tar_store.strong_ref()).unwrap();
    }
}
