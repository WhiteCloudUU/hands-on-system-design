use async_trait::async_trait;
use dashmap::DashMap;
use std::sync::{Arc, Mutex};

use crate::rate_limiting_algo::TokenBucket;

// Trait that represents a rate-limiter placement API.
#[async_trait(?Send)]
pub trait RateLimiter: Send + Sync + 'static {
    // Check a request for the given client: returns
    // (allowed, limit, remaining, reset_seconds)
    async fn is_allowed(&self, client_id: &str) -> (bool, u64, u64, u64);
}

/// In-process (local) limiter: quick, low-latency, but per-instance state (no global enforcement).
pub struct InProcLimiter {
    map: DashMap<String, Arc<Mutex<TokenBucket>>>, // map client_id -> Mutex<TokenBucket>
    capacity: f64,
    refill_rate: f64,
}

impl InProcLimiter {
    pub fn new(capacity: f64, refill_rate: f64) -> Self {
        Self {
            map: DashMap::new(),
            capacity,
            refill_rate,
        }
    }

    fn get_bucket(&self, client: &str) -> Arc<Mutex<TokenBucket>> {
        if let Some(e) = self.map.get(client) {
            e.clone()
        } else {
            let bucket = Arc::new(Mutex::new(TokenBucket::new(
                self.capacity,
                self.refill_rate,
            )));
            self.map.insert(client.to_string(), bucket.clone());

            bucket
        }
    }
}

#[async_trait::async_trait(?Send)]
impl RateLimiter for InProcLimiter {
    async fn is_allowed(&self, client_id: &str) -> (bool, u64, u64, u64) {
        let bucket = self.get_bucket(client_id);

        let mut guard = bucket.lock().unwrap();
        let (allowed, remaining, reset_seconds) = guard.try_consume();

        let limit = self.capacity as u64;

        (allowed, limit, remaining, reset_seconds)
    }
}
