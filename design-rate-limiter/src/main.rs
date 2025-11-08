use std::sync::Arc;

use actix_web::{App, HttpRequest, HttpServer, Responder, web};

use crate::middleware::RateLimitMiddleware;
use crate::rate_limiter::{InProcLimiter, RateLimiter};

mod middleware;
mod rate_limiter;
mod rate_limiting_algo;

// Simple handler
async fn hello(req: HttpRequest) -> impl Responder {
    let api_key = req
        .headers()
        .get("x-api-key")
        .and_then(|h| h.to_str().ok())
        .unwrap_or("<none>");
    format!("Hello! your api key: {}", api_key)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Choose placement: comment/uncomment to switch
    // 1) In-process (low-latency, per-instance)
    let limiter: Arc<dyn RateLimiter> = Arc::new(InProcLimiter::new(2.0, 0.0)); // capacity = 5 tokens, refill 1 token/sec

    // 2) Remote (centralized) example with simulated latency:
    // let limiter: Arc<dyn RateLimiter> = Arc::new(RemoteLimiter::new(10.0, 2.0, Duration::from_millis(10)));

    println!("Starting server at http://127.0.0.1:8080");
    HttpServer::new(move || {
        App::new()
            // attach middleware
            .wrap(RateLimitMiddleware {
                limiter: limiter.clone(),
            })
            .route("/", web::get().to(hello))
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}
