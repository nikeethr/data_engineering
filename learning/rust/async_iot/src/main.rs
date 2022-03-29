mod requests;

use tokio::net::TcpListener;
use tokio::io::{AsyncReadExt, AsyncWriteExt};


fn setup_logger() {
    let logger = femme::pretty::Logger::new();
    async_log::Logger::wrap(logger, || 12)
        .start(log::LevelFilter::Trace)
        .unwrap();
}

#[macro_use]
extern crate lazy_static;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    setup_logger();
    let res = requests::hive::get_farm_ids().await;
    res.into_iter().for_each(|s| {
        println!("{:?}", s);
    });
    Ok(())
}
