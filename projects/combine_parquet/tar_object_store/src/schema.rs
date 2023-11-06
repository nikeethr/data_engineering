// get schema for all fields
// deserialize

use arrow::datatypes::SchemaBuilder;
use bytes::{buf::Buf, buf::Reader, Bytes};
use datafusion::datasource::listing::ListingTableInsertMode;
use datafusion::prelude::*;
use datafusion::sql::sqlparser::ast::SchemaName;
use object_store::{memory::InMemory, ObjectStore};
use serde::Serialize;
use serde_json::Serializer;
use std::fmt::Debug;
use std::fs::File;
use std::io::{BufReader, Read, Seek, Write};
use std::sync::{Arc, Weak};
use tar::{Archive, Entry};
use tokio::runtime::Handle;
use url::Url;

use datafusion::arrow::datatypes::{DataType, Field, Schema, SchemaRef};

const REFERENCE_ENTRY_PATH: &'static str = "mem://reference_entry.pq";

pub fn infer_schema_from_first_obj(
    input_tar_path: String,
    output_path: String,
    prefix: Option<String>,
) -> tokio::io::Result<()> {
    // extract entry
    let mut ta = Archive::new(File::open(input_tar_path).unwrap());

    let entry = extract_one_entry(&mut ta, prefix).expect("Could not extract a valid entry.");

    let schema = tokio::runtime::Builder::new_multi_thread()
        .build()
        .unwrap()
        .block_on(async move {
            // TODO: arc objects should probably be created in the context that the data is created..??
            // i.e. fn(Arc<something>) -> Arc<anotherthing> ??
            let mut entry = entry;
            let mem_store = Arc::new(
                load_into_memory_store(
                    Arc::get_mut(&mut entry).expect("Unable to get entry as mut"),
                )
                .await
                .unwrap(),
            );

            get_schema_from_memory_store(mem_store).await.unwrap()
        });

    // spit out metadata to file
    Ok(serde_json::to_writer(
        File::create(output_path).unwrap(),
        &SchemaRef::into_inner(schema).unwrap(),
    )?)
}

pub fn deserialize(schema_ref_path: String) -> serde_json::Result<Schema> {
    serde_json::from_reader::<File, Schema>(File::open(schema_ref_path).unwrap())
}

async fn get_schema_from_memory_store(mem_store: Arc<InMemory>) -> tokio::io::Result<SchemaRef> {
    let ctx = SessionContext::new();

    ctx.runtime_env()
        .register_object_store(&Url::parse("mem://").unwrap(), mem_store);

    let mut options = ParquetReadOptions::default();
    options.file_extension = ".pq";
    options.insert_mode = ListingTableInsertMode::Error;

    ctx.register_parquet("entry_schema", REFERENCE_ENTRY_PATH, options);

    Ok(SchemaRef::new(Schema::from(
        ctx.table("entry_schema").await?.schema(),
    )))
}

async fn load_into_memory_store<'a>(entry: &mut Entry<'a, File>) -> tokio::io::Result<InMemory> {
    let store = InMemory::new();
    let location = object_store::path::Path::from(REFERENCE_ENTRY_PATH);
    let mut buffer = Vec::<u8>::new();
    entry.read_to_end(&mut buffer);
    store.put(&location, Bytes::from_iter(buffer));

    Ok(store)
}

fn extract_one_entry<'a>(
    ta: &'a mut Archive<File>,
    prefix: Option<String>,
) -> Result<Arc<Entry<'a, File>>, std::io::Error> {
    Ok(Arc::new(match prefix {
        Some(s) => ta
            .entries_with_seek()?
            .filter_map(|e| e.ok())
            .find(|e| e.path().unwrap().starts_with(s.to_owned()))
            .unwrap(),
        None => ta.entries_with_seek()?.next().unwrap().unwrap(),
    }))
}
