mod routes;
mod services;

use actix_web::{web, App, HttpServer};

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("Starting server at http://127.0.0.1:8080");
    HttpServer::new(|| {
        App::new()
            .route(
                "/upload",
                web::post().to(routes::simple_upload::request_upload_permission),
            )
            .route(
                "/initiate_upload",
                web::post().to(routes::resumable_upload::initiate_upload),
            )
            .route(
                "/upload_block",
                web::post().to(routes::resumable_upload::upload_block),
            )
            .route(
                "/commit_upload",
                web::post().to(routes::resumable_upload::commit_upload),
            )
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}
