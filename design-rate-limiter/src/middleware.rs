use std::sync::Arc;
use std::task::{Context, Poll};

use actix_web::body::MessageBody;
use actix_web::{
    Error, HttpResponse,
    body::BoxBody,
    dev::{ServiceRequest, ServiceResponse, Transform},
    http::header,
};
use futures_util::future::{self, LocalBoxFuture, Ready};

use crate::rate_limiter::RateLimiter;

/// Middleware which:
/// identifies client -> picks limiter -> checks -> either continues or returns 429.
pub struct RateLimitMiddleware {
    pub limiter: Arc<dyn RateLimiter>,
}

impl<S, B> Transform<S, ServiceRequest> for RateLimitMiddleware
where
    S: actix_web::dev::Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error>
        + 'static,
    S::Future: 'static,
    B: MessageBody + 'static,
{
    type Response = ServiceResponse<BoxBody>;
    type Error = Error;
    type InitError = ();
    type Transform = RateLimitMiddlewareService<S>;
    type Future = Ready<Result<Self::Transform, Self::InitError>>;

    fn new_transform(&self, service: S) -> Self::Future {
        future::ok(RateLimitMiddlewareService {
            service: std::sync::Arc::new(service),
            limiter: self.limiter.clone(),
        })
    }
}

pub struct RateLimitMiddlewareService<S> {
    service: std::sync::Arc<S>,
    limiter: Arc<dyn RateLimiter>,
}

impl<S, B> actix_web::dev::Service<ServiceRequest> for RateLimitMiddlewareService<S>
where
    S: actix_web::dev::Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error>
        + 'static,
    S::Future: 'static,
    B: MessageBody + 'static,
{
    type Response = ServiceResponse<BoxBody>;
    type Error = Error;
    type Future = LocalBoxFuture<'static, Result<Self::Response, Self::Error>>;

    fn poll_ready(&self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.service.poll_ready(cx)
    }

    fn call(&self, req: ServiceRequest) -> Self::Future {
        // Identify client: prefer x-api-key header, else peer ip
        let limiter = self.limiter.clone();
        let (http_req, payload) = req.into_parts();
        let headers = http_req.headers().clone();

        // Extract client id here synchronously
        let client_id = headers
            .get("x-api-key")
            .and_then(|hv| hv.to_str().ok())
            .map(|s| s.to_string())
            .or_else(|| {
                // fallback: peer addr (note: may be None in some environments)
                http_req.peer_addr().map(|addr| addr.ip().to_string())
            })
            .unwrap_or_else(|| "unknown_client".to_string());

        let svc = self.service.clone();

        Box::pin(async move {
            let (allowed, limit, remaining, reset_secs) = limiter.is_allowed(&client_id).await;

            if allowed {
                // rebuild request and call inner service
                let req = ServiceRequest::from_parts(http_req, payload);
                let res = svc.call(req).await?;

                // inject rate limit headers into successful response as example
                let mut res = res.map_into_boxed_body();
                res.response_mut().headers_mut().insert(
                    header::HeaderName::from_static("x-ratelimit-limit"),
                    header::HeaderValue::from_str(&format!("{}", limit)).unwrap(),
                );
                res.response_mut().headers_mut().insert(
                    header::HeaderName::from_static("x-ratelimit-remaining"),
                    header::HeaderValue::from_str(&format!("{}", remaining)).unwrap(),
                );
                res.response_mut().headers_mut().insert(
                    header::HeaderName::from_static("x-ratelimit-reset"),
                    header::HeaderValue::from_str(&format!("{}", reset_secs)).unwrap(),
                );
                Ok(res)
            } else {
                // When limits exceeded: fail fast with 429 and headers
                let mut builder = HttpResponse::TooManyRequests();
                builder.insert_header(("x-ratelimit-limit", format!("{}", limit)));
                builder.insert_header(("x-ratelimit-remaining", format!("{}", remaining)));
                builder.insert_header(("x-ratelimit-reset", format!("{}", reset_secs)));
                // Optional Retry-After header
                builder.insert_header(("retry-after", format!("{}", reset_secs)));
                let body = format!("rate limit exceeded for client {}", client_id);
                let resp = builder.body(body);
                // convert into ServiceResponse<BoxBody>
                let srv_resp = ServiceResponse::new(http_req, resp.map_into_boxed_body());
                Ok(srv_resp)
            }
        })
    }
}
