// TODO: how to export/load this module

use std::string::String;
use serde_json::from_value;
use std::collections::HashMap;
use log::info;

// TODO: pick up API_URI and API_KEY from config file
static API_URI: &str = "https://api2.hiveos.farm/api/v2";
static API_KEY: &str = "";

lazy_static::lazy_static! {
    pub static ref HTTP_CLIENT: reqwest::Client = reqwest::Client::new();
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
    ].into_iter().for_each(|(k, v)| {
        headers.insert(k, v);
    });
    headers
}

// TODO: this function is probabl not required
fn generic_request_builder(api_path: String) -> reqwest::RequestBuilder {
    HTTP_CLIENT.get(api_path)
}

// TODO: try using a struct for deserializing
fn deserialize_farm_ids(resp: serde_json::Value) -> Vec<String> {
    let r: HashMap<String, serde_json::Value> = from_value(resp).unwrap();
    let data: Vec<serde_json::Value> = from_value(r["data"].clone()).unwrap();
    data.into_iter().map(|v| {
        let elem: HashMap<String, serde_json::Value> = from_value(v).unwrap();
        let farm_id: String = from_value::<u64>(elem["id"].clone()).unwrap().to_string();
        return farm_id;
    }).collect::<Vec<String>>()
}

pub async fn get_farm_ids() -> Vec<String> {
    let resp = generic_request_builder(format!("{}/farms", API_URI))
        .headers(generic_headers())
        .send()
        .await;

    match resp {
        Ok(r) => {
            match r.json().await {
                Ok(d) => {
                    return deserialize_farm_ids(d);
                },
                Err(_e) => return Vec::<String>::new(),
            };
        },
        Err(_e) => return Vec::<String>::new(),
    };
}
