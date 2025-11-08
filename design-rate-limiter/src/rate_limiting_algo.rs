use std::time::Instant;

#[derive(Debug)]
pub struct TokenBucket {
    capacity: f64,          // max tokens
    tokens: f64,            // current tokens (can be fractional)
    tokens_per_second: f64, // refill rate
    last_refill: Instant,
}

impl TokenBucket {
    pub fn new(capacity: f64, tokens_per_second: f64) -> Self {
        Self {
            capacity,
            tokens: capacity,
            tokens_per_second,
            last_refill: Instant::now(),
        }
    }

    // Try to consume 1 token. Return (allowed, remaining_tokens, seconds_until_full)
    pub fn try_consume(&mut self) -> (bool, u64, u64) {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_refill).as_secs_f64();
        if elapsed > 0.0 {
            self.tokens = (self.tokens + elapsed * self.tokens_per_second).min(self.capacity);
            self.last_refill = now;
        }

        if self.tokens >= 1.0 {
            self.tokens -= 1.0;
            let remaining = self.tokens.floor() as u64;
            let seconds_until_full = if self.tokens >= self.capacity {
                0
            } else {
                ((self.capacity - self.tokens) / self.tokens_per_second).ceil() as u64
            };
            (true, remaining, seconds_until_full)
        } else {
            let remaining = self.tokens.floor() as u64;
            let missing = self.capacity - self.tokens;
            let seconds_until_full = (missing / self.tokens_per_second).ceil() as u64;
            (false, remaining, seconds_until_full)
        }
    }
}
