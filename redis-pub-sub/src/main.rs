use redis::Commands;
use std::thread;
use std::time::Duration;

fn main() -> redis::RedisResult<()> {
    // Connect to local Redis server
    let client = redis::Client::open("redis://127.0.0.1/")?;

    // --- Publisher Thread ---
    let publisher = client.clone();
    thread::spawn(move || {
        let mut conn = publisher.get_connection().unwrap();
        for i in 1..=5 {
            let msg = format!("hello #{i}");
            let _: () = conn.publish("my-channel", msg.clone()).unwrap();
            println!("Published: {}", msg);
            thread::sleep(Duration::from_secs(1));
        }
    });

    // --- Subscriber Thread ---
    let mut conn = client.get_connection()?;
    let mut pubsub = conn.as_pubsub();
    pubsub.subscribe("my-channel")?;
    println!("Subscribed to 'my-channel'");

    // Listen for messages - polling
    loop {
        let msg = pubsub.get_message()?;
        let payload: String = msg.get_payload()?;
        println!("Received: {}", payload);

        if payload.contains("5") {
            println!("Exiting after last message...");
            break;
        }
    }

    Ok(())
}
