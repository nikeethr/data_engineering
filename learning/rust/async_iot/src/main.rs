mod requests;

use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;

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
    match res {
        Ok(r) => {
            r.into_iter().for_each(|s| {
                println!("{:?}", s);
            });
        }
        Err(e) => println!("{:?}", e),
    }
    Ok(())
}
