class RateLimiter {
  constructor(maxRequests = 100, windowMs = 60000) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
    this.requests = new Map();
  }

  isAllowed(key = 'default') {
    const now = Date.now();
    const userRequests = this.requests.get(key) || [];
    
    // Remove old requests outside the window
    const validRequests = userRequests.filter(
      timestamp => now - timestamp < this.windowMs
    );
    
    if (validRequests.length >= this.maxRequests) {
      return {
        allowed: false,
        remaining: 0,
        resetTime: Math.min(...validRequests) + this.windowMs
      };
    }
    
    // Add current request
    validRequests.push(now);
    this.requests.set(key, validRequests);
    
    return {
      allowed: true,
      remaining: this.maxRequests - validRequests.length,
      resetTime: validRequests[0] + this.windowMs
    };
  }

  getRemainingRequests(key = 'default') {
    const now = Date.now();
    const userRequests = this.requests.get(key) || [];
    const validRequests = userRequests.filter(
      timestamp => now - timestamp < this.windowMs
    );
    
    return Math.max(0, this.maxRequests - validRequests.length);
  }

  reset(key = 'default') {
    this.requests.delete(key);
  }

  resetAll() {
    this.requests.clear();
  }
}

// API-specific rate limiters
export const rateLimiters = {
  transcription: new RateLimiter(10, 60000), // 10 requests per minute
  search: new RateLimiter(30, 60000), // 30 requests per minute
  export: new RateLimiter(20, 60000), // 20 exports per minute
  general: new RateLimiter(100, 60000) // 100 general requests per minute
};

export default RateLimiter;