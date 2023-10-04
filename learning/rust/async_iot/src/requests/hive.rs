// TODO: how to export/load this module

use log::info;
use serde::Deserialize;
use serde_json::from_value;
use std::collections::HashMap;
use std::string::String;

// TODO: pick up API_URI and API_KEY from config file
// https://app.swaggerhub.com/apis/HiveOS/public/2.1-beta
static API_URI: &str = "https://api2.hiveos.farm/api/v2";
static API_KEY: &str = "";

lazy_static::lazy_static! {
    pub static ref HTTP_CLIENT: reqwest::Client = reqwest::Client::new();
}

#[derive(serde::Deserialize)]
struct FarmsResponse {
    data: Vec<FarmData>,
}

#[derive(serde::Deserialize)]
struct FarmData {
    id: u32,
}

fn generic_headers() -> reqwest::header::HeaderMap {
    let mut headers = reqwest::header::HeaderMap::new();
    vec![
        (
            reqwest::header::AUTHORIZATION,
            reqwest::header::HeaderValue::from_str(format!("Bearer {}", API_KEY).as_str()).unwrap(),
        ),
        (
            reqwest::header::ACCEPT,
            reqwest::header::HeaderValue::from_str("application/json").unwrap(),
        ),
    ]
    .into_iter()
    .for_each(|(k, v)| {
        headers.insert(k, v);
    });
    headers
}

async fn deserialize_farm_ids(
    resp: reqwest::Response,
) -> Result<Vec<String>, Box<dyn std::error::Error>> {
    Ok(resp
        .json::<FarmsResponse>()
        .await?
        .data
        .into_iter()
        .map(|farm| farm.id.to_string())
        .collect::<Vec<String>>())
}

pub async fn get_farm_ids() -> Result<Vec<String>, Box<dyn std::error::Error>> {
    Ok(deserialize_farm_ids(
        HTTP_CLIENT
            .get(format!("{}/farms", API_URI))
            .headers(generic_headers())
            .send()
            .await?,
    )
    .await?)
}
