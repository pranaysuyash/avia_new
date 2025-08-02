-- Production database initialization script
-- Audio/Video Transcription Platform

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false
);

-- Transcriptions table
CREATE TABLE IF NOT EXISTS transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    original_text TEXT,
    language VARCHAR(10),
    duration INTEGER, -- in seconds
    word_count INTEGER,
    confidence FLOAT,
    processing_time FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    file_url VARCHAR(500),
    file_size BIGINT,
    status VARCHAR(50) DEFAULT 'processing',
    model_used VARCHAR(100),
    metadata JSONB
);

-- Speaker segments table
CREATE TABLE IF NOT EXISTS speaker_segments (
    id SERIAL PRIMARY KEY,
    transcription_id UUID REFERENCES transcriptions(id) ON DELETE CASCADE,
    speaker_id VARCHAR(100) NOT NULL,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    text TEXT,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Named entities table
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    transcription_id UUID REFERENCES transcriptions(id) ON DELETE CASCADE,
    text VARCHAR(255) NOT NULL,
    label VARCHAR(100) NOT NULL,
    start_pos INTEGER,
    end_pos INTEGER,
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Content insights table
CREATE TABLE IF NOT EXISTS content_insights (
    id SERIAL PRIMARY KEY,
    transcription_id UUID REFERENCES transcriptions(id) ON DELETE CASCADE,
    summary TEXT,
    action_items JSONB,
    sentiment_data JSONB,
    topics JSONB,
    key_highlights JSONB,
    meeting_minutes JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    permissions JSONB,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET
);

-- Usage analytics table
CREATE TABLE IF NOT EXISTS usage_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_transcriptions_user_id ON transcriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_transcriptions_created_at ON transcriptions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transcriptions_status ON transcriptions(status);
CREATE INDEX IF NOT EXISTS idx_transcriptions_language ON transcriptions(language);

CREATE INDEX IF NOT EXISTS idx_speaker_segments_transcription_id ON speaker_segments(transcription_id);
CREATE INDEX IF NOT EXISTS idx_speaker_segments_speaker_id ON speaker_segments(speaker_id);
CREATE INDEX IF NOT EXISTS idx_speaker_segments_time ON speaker_segments(start_time, end_time);

CREATE INDEX IF NOT EXISTS idx_entities_transcription_id ON entities(transcription_id);
CREATE INDEX IF NOT EXISTS idx_entities_label ON entities(label);
CREATE INDEX IF NOT EXISTS idx_entities_text_gin ON entities USING gin(text gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_content_insights_transcription_id ON content_insights(transcription_id);

CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);

CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_id ON usage_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_action ON usage_analytics(action);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_created_at ON usage_analytics(created_at DESC);

-- Full-text search index for transcriptions
CREATE INDEX IF NOT EXISTS idx_transcriptions_text_search ON transcriptions USING gin(to_tsvector('english', original_text));

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_transcriptions_updated_at BEFORE UPDATE ON transcriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_insights_updated_at BEFORE UPDATE ON content_insights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password: admin123 - change in production!)
INSERT INTO users (email, password_hash, name, subscription_tier, is_active, email_verified)
VALUES (
    'admin@yourdomain.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeU' || 'some_secure_hash',
    'Administrator',
    'enterprise',
    true,
    true
) ON CONFLICT (email) DO NOTHING;

-- Create view for user statistics
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.email,
    u.name,
    u.subscription_tier,
    COUNT(t.id) as total_transcriptions,
    COALESCE(SUM(t.duration), 0) as total_duration_seconds,
    COALESCE(SUM(t.word_count), 0) as total_words,
    AVG(t.confidence) as avg_confidence,
    MAX(t.created_at) as last_transcription_at
FROM users u
LEFT JOIN transcriptions t ON u.id = t.user_id
GROUP BY u.id, u.email, u.name, u.subscription_tier;

-- Create view for transcription analytics
CREATE OR REPLACE VIEW transcription_analytics AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_transcriptions,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_transcriptions,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_transcriptions,
    AVG(CASE WHEN status = 'completed' THEN processing_time END) as avg_processing_time,
    AVG(CASE WHEN status = 'completed' THEN confidence END) as avg_confidence,
    SUM(CASE WHEN status = 'completed' THEN duration ELSE 0 END) as total_audio_duration
FROM transcriptions
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Grant permissions (adjust as needed)
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO transcription_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO transcription_user;
GRANT SELECT ON user_stats, transcription_analytics TO transcription_user;

-- Create database maintenance functions
CREATE OR REPLACE FUNCTION cleanup_old_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM user_sessions WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cleanup_old_analytics(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM usage_analytics WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create maintenance schedule (requires pg_cron extension - install separately)
-- SELECT cron.schedule('cleanup-sessions', '0 2 * * *', 'SELECT cleanup_old_sessions();');
-- SELECT cron.schedule('cleanup-analytics', '0 3 * * 0', 'SELECT cleanup_old_analytics(90);');