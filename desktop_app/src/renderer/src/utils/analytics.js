class Analytics {
  constructor() {
    this.events = [];
    this.session = {
      id: this.generateSessionId(),
      startTime: new Date(),
      userId: localStorage.getItem('userId') || 'anonymous'
    };
    this.apiUsage = {
      transcriptions: 0,
      searches: 0,
      exports: 0,
      errors: 0,
      totalRequests: 0
    };
    this.loadStoredData();
  }

  generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  loadStoredData() {
    try {
      const storedUsage = localStorage.getItem('apiUsage');
      if (storedUsage) {
        this.apiUsage = { ...this.apiUsage, ...JSON.parse(storedUsage) };
      }
      
      const storedEvents = localStorage.getItem('analyticsEvents');
      if (storedEvents) {
        this.events = JSON.parse(storedEvents);
      }
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    }
  }

  saveData() {
    try {
      localStorage.setItem('apiUsage', JSON.stringify(this.apiUsage));
      // Only keep last 1000 events
      const recentEvents = this.events.slice(-1000);
      localStorage.setItem('analyticsEvents', JSON.stringify(recentEvents));
    } catch (error) {
      console.error('Failed to save analytics data:', error);
    }
  }

  trackEvent(category, action, label = null, value = null) {
    const event = {
      category,
      action,
      label,
      value,
      timestamp: new Date().toISOString(),
      sessionId: this.session.id,
      userId: this.session.userId
    };
    
    this.events.push(event);
    this.saveData();
    
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log('Analytics Event:', event);
    }
  }

  trackAPICall(endpoint, method = 'GET', status = 200, duration = 0) {
    this.apiUsage.totalRequests++;
    
    // Track specific endpoint usage
    if (endpoint.includes('transcription')) {
      this.apiUsage.transcriptions++;
    } else if (endpoint.includes('search')) {
      this.apiUsage.searches++;
    } else if (endpoint.includes('export')) {
      this.apiUsage.exports++;
    }
    
    // Track errors
    if (status >= 400) {
      this.apiUsage.errors++;
    }
    
    this.trackEvent('API', method, endpoint, {
      status,
      duration,
      timestamp: new Date().toISOString()
    });
    
    this.saveData();
  }

  getUsageStats() {
    const sessionDuration = (new Date() - new Date(this.session.startTime)) / 1000; // in seconds
    
    return {
      session: {
        ...this.session,
        duration: sessionDuration
      },
      apiUsage: {
        ...this.apiUsage,
        successRate: this.apiUsage.totalRequests > 0 
          ? ((this.apiUsage.totalRequests - this.apiUsage.errors) / this.apiUsage.totalRequests * 100).toFixed(2) 
          : 100
      },
      hourlyDistribution: this.getHourlyDistribution(),
      topEndpoints: this.getTopEndpoints(),
      errorRate: this.getErrorRate()
    };
  }

  getHourlyDistribution() {
    const distribution = Array(24).fill(0);
    const now = new Date();
    const twentyFourHoursAgo = new Date(now - 24 * 60 * 60 * 1000);
    
    this.events
      .filter(event => new Date(event.timestamp) > twentyFourHoursAgo)
      .forEach(event => {
        const hour = new Date(event.timestamp).getHours();
        distribution[hour]++;
      });
    
    return distribution;
  }

  getTopEndpoints() {
    const endpointCounts = {};
    
    this.events
      .filter(event => event.category === 'API')
      .forEach(event => {
        const endpoint = event.label;
        endpointCounts[endpoint] = (endpointCounts[endpoint] || 0) + 1;
      });
    
    return Object.entries(endpointCounts)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10)
      .map(([endpoint, count]) => ({ endpoint, count }));
  }

  getErrorRate() {
    const recentEvents = this.events.filter(
      event => event.category === 'API' && 
      new Date(event.timestamp) > new Date(Date.now() - 60 * 60 * 1000) // Last hour
    );
    
    const errors = recentEvents.filter(event => event.value?.status >= 400);
    
    return {
      lastHour: recentEvents.length > 0 
        ? (errors.length / recentEvents.length * 100).toFixed(2) 
        : 0,
      total: this.apiUsage.totalRequests > 0 
        ? (this.apiUsage.errors / this.apiUsage.totalRequests * 100).toFixed(2) 
        : 0
    };
  }

  // Feature usage tracking
  trackFeatureUsage(feature, action = 'used') {
    this.trackEvent('Feature', action, feature);
  }

  // Performance tracking
  trackPerformance(metric, value) {
    this.trackEvent('Performance', metric, null, value);
  }

  // User action tracking
  trackUserAction(action, details = null) {
    this.trackEvent('User', action, details);
  }

  // Export analytics data
  exportAnalytics() {
    const data = {
      session: this.session,
      apiUsage: this.apiUsage,
      events: this.events,
      stats: this.getUsageStats(),
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics_${this.session.id}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Clear analytics data
  clearAnalytics() {
    this.events = [];
    this.apiUsage = {
      transcriptions: 0,
      searches: 0,
      exports: 0,
      errors: 0,
      totalRequests: 0
    };
    localStorage.removeItem('apiUsage');
    localStorage.removeItem('analyticsEvents');
  }
}

// Create singleton instance
const analytics = new Analytics();

export default analytics;