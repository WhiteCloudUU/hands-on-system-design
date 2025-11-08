use crate::services;
use actix_web::{web, HttpResponse};
use serde::Deserialize;

#[derive(Deserialize)]
pub struct UploadRequest {
    pub user_id: String,
    pub file_name: String,
}

// Handles the upload permission request and presigned URL generation
pub async fn request_upload_permission(req: web::Json<UploadRequest>) -> HttpResponse {
    let user_id = &req.user_id;
    let file_name = &req.file_name;

    if !services::user::validate_user(user_id) {
        return HttpResponse::Unauthorized().body("Invalid user");
    }

    if !services::user::check_quota(user_id) {
        return HttpResponse::Forbidden().body("Quota exceeded");
    }

    let presigned_url = services::presign::generate_presigned_url(file_name, 3600);

    HttpResponse::Ok().json(serde_json::json!({
        "presigned_url": presigned_url
    }))
}
