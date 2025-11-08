use reqwest::Client;
use serde_json::json;
use std::error::Error;
use std::fs;

/*
1. Initiat upload -> 拿到presigned url,
*/
#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let file_path = "prompts.txt";
    let user_id = "testuser";
    let file_name = "prompt.txt";
    let file_bytes = fs::read(file_path)?;
    println!(
        "Uploading {}... File size: {} bytes",
        file_name,
        file_bytes.len()
    );

    let client = Client::new();
    // 1. Initiate upload
    let resp = client
        .post("http://localhost:8080/initiate_upload")
        .json(&json!({"user_id": user_id, "file_name": file_name}))
        .send()
        .await?;
    let resp_json: serde_json::Value = resp.json().await?;
    let upload_id = resp_json["upload_id"].as_str().unwrap();
    let block_size = resp_json["block_size"].as_u64().unwrap() as usize;
    println!("Upload ID: {}. Block size: {}", upload_id, block_size);

    // 2. Split file and upload blocks
    let mut block_ids = Vec::new();
    for (i, chunk) in file_bytes.chunks(block_size).enumerate() {
        let block_id = base64::encode(format!("{:06}", i));
        block_ids.push(block_id.clone());
        let resp = client
            .post("http://localhost:8080/upload_block")
            .json(&json!({
                "upload_id": upload_id,
                "block_id": block_id,
                "data": chunk
            }))
            .send()
            .await?;
        println!(
            "Block {} with id {} uploaded status: {}",
            i,
            block_id,
            resp.status()
        );
    }

    // 3. Commit upload
    let resp = client
        .post("http://localhost:8080/commit_upload")
        .json(&json!({
            "upload_id": upload_id,
            "block_ids": block_ids
        }))
        .send()
        .await?;
    println!("Commit response: {}", resp.status());

    Ok(())
}
