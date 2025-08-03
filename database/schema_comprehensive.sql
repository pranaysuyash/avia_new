-- Comprehensive PostgreSQL Schema for Audio/Video Transcription Platform
-- Version: 2.0
-- Covers all features: transcription, collaboration, teams, sharing, analytics, etc.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- For UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- For encryption functions
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- For composite GIN indexes

-- Drop existing tables if needed (BE CAREFUL IN PRODUCTION!)
-- Uncomment only for fresh installations
-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;

-- ===========================================
-- ENUMS
-- ===========================================

-- User roles
CREATE TYPE user_role AS ENUM ('user', 'admin', 'viewer', 'moderator');

-- Subscription tiers
CREATE TYPE subscription_tier AS ENUM ('free', 'basic', 'pro', 'enterprise');

-- Share permissions
CREATE TYPE share_permission AS ENUM ('view', 'comment', 'edit', 'admin');

-- Team roles
CREATE TYPE team_role AS ENUM ('owner', 'admin', 'member', 'viewer');

-- Processing status
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');

-- Transcription models
CREATE TYPE ai_model AS ENUM ('whisper-tiny', 'whisper-base', 'whisper-small', 'whisper-medium', 'whisper-large', 'openai-whisper', 'custom');

-- Entity types
CREATE TYPE entity_type AS ENUM ('person', 'organization', 'location', 'date', 'time', 'money', 'percentage', 'product', 'event', 'email', 'phone', 'url', 'custom');

-- Content types
CREATE TYPE content_type AS ENUM ('meeting', 'interview', 'lecture', 'podcast', 'conversation', 'presentation', 'other');

-- Export formats
CREATE TYPE export_format AS ENUM ('txt', 'docx', 'pdf', 'srt', 'vtt', 'json', 'csv');

-- Notification types
CREATE TYPE notification_type AS ENUM ('mention', 'share', 'comment', 'transcript_ready', 'team_invite', 'quota_warning', 'system');

-- ===========================================
-- CORE TABLES
-- ===========================================

-- Users table (authentication and profile)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    phone VARCHAR(50),
    
    -- Account settings
    role user_role DEFAULT 'user',
    subscription_tier subscription_tier DEFAULT 'free',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),
    
    -- Tokens
    verification_token VARCHAR(100) UNIQUE,
    reset_token VARCHAR(100) UNIQUE,
    reset_token_expires TIMESTAMP,
    
    -- Quotas and limits
    storage_quota_mb INTEGER DEFAULT 5000,
    storage_used_mb DECIMAL(10,2) DEFAULT 0,
    monthly_minutes_quota INTEGER DEFAULT 300,
    monthly_minutes_used DECIMAL(10,2) DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE,
    
    -- Preferences (JSON)
    preferences JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{"email": true, "push": true, "sms": false}'
);

-- Sessions table (JWT and session management)
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE,
    
    -- Session info
    ip_address INET,
    user_agent TEXT,
    device_info JSONB,
    
    -- Validity
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    
    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_token (session_token),
    INDEX idx_sessions_expires (expires_at)
);

-- API Keys table
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(10) NOT NULL, -- First few chars for identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Permissions and limits
    permissions JSONB DEFAULT '{}',
    rate_limit INTEGER DEFAULT 1000, -- requests per hour
    
    -- Usage tracking
    last_used TIMESTAMP WITH TIME ZONE,
    total_requests INTEGER DEFAULT 0,
    
    -- Validity
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_api_keys_user_id (user_id),
    INDEX idx_api_keys_hash (key_hash),
    INDEX idx_api_keys_prefix (key_prefix)
);

-- ===========================================
-- TEAMS AND COLLABORATION
-- ===========================================

-- Teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    avatar_url VARCHAR(500),
    
    -- Ownership
    owner_id INTEGER REFERENCES users(id) ON DELETE RESTRICT,
    
    -- Settings
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false,
    max_members INTEGER DEFAULT 10,
    
    -- Quotas
    storage_quota_mb INTEGER DEFAULT 50000,
    storage_used_mb DECIMAL(10,2) DEFAULT 0,
    monthly_minutes_quota INTEGER DEFAULT 3000,
    monthly_minutes_used DECIMAL(10,2) DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Settings
    settings JSONB DEFAULT '{}'
);

-- Team members table
CREATE TABLE team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role team_role DEFAULT 'member',
    
    -- Invitation tracking
    invited_by_id INTEGER REFERENCES users(id),
    invitation_token VARCHAR(100) UNIQUE,
    invitation_accepted BOOLEAN DEFAULT false,
    
    -- Timestamps
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    invited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(team_id, user_id),
    INDEX idx_team_members_team (team_id),
    INDEX idx_team_members_user (user_id)
);

-- Projects within teams
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    color VARCHAR(7), -- Hex color
    icon VARCHAR(50), -- Icon name
    
    -- Ownership
    created_by_id INTEGER REFERENCES users(id),
    
    -- Status
    is_archived BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(team_id, slug),
    INDEX idx_projects_team (team_id)
);

-- ===========================================
-- TRANSCRIPTION TABLES
-- ===========================================

-- Main transcripts table
CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Ownership
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    
    -- Basic info
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content TEXT NOT NULL, -- Full transcript text
    
    -- File information
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_url VARCHAR(1000),
    file_size BIGINT,
    file_hash VARCHAR(64), -- SHA256 hash for deduplication
    mime_type VARCHAR(100),
    
    -- Processing info
    status processing_status DEFAULT 'pending',
    model_used ai_model,
    processing_time DECIMAL(10,2), -- seconds
    error_message TEXT,
    
    -- Content metadata
    language VARCHAR(10) DEFAULT 'en',
    duration DECIMAL(10,2), -- seconds
    word_count INTEGER,
    confidence DECIMAL(5,4), -- 0.0000 to 1.0000
    
    -- Content analysis
    content_type content_type,
    summary TEXT,
    key_points TEXT[],
    action_items JSONB,
    topics TEXT[],
    sentiment_score DECIMAL(3,2), -- -1.00 to 1.00
    
    -- Visibility
    is_public BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_transcripts_user (user_id),
    INDEX idx_transcripts_team (team_id),
    INDEX idx_transcripts_project (project_id),
    INDEX idx_transcripts_status (status),
    INDEX idx_transcripts_created (created_at DESC),
    INDEX idx_transcripts_hash (file_hash)
);

-- Full-text search index
CREATE INDEX idx_transcripts_fts ON transcripts 
USING gin(to_tsvector('english', content || ' ' || COALESCE(title, '') || ' ' || COALESCE(summary, '')));

-- Speaker diarization results
CREATE TABLE speaker_segments (
    id SERIAL PRIMARY KEY,
    transcript_id UUID REFERENCES transcripts(id) ON DELETE CASCADE,
    
    -- Speaker info
    speaker_id VARCHAR(50) NOT NULL,
    speaker_name VARCHAR(100), -- User-assigned name
    speaker_label VARCHAR(50), -- Auto-generated label (Speaker 1, etc.)
    
    -- Segment timing
    start_time DECIMAL(10,3) NOT NULL,
    end_time DECIMAL(10,3) NOT NULL,
    
    -- Content
    text TEXT NOT NULL,
    word_count INTEGER,
    confidence DECIMAL(5,4),
    
    -- Voice characteristics (from analysis)
    voice_embedding VECTOR(256), -- If using pgvector
    voice_characteristics JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_speaker_segments_transcript (transcript_id),
    INDEX idx_speaker_segments_speaker (speaker_id),
    INDEX idx_speaker_segments_time (transcript_id, start_time, end_time)
);

-- Named entities extracted
CREATE TABLE entities (
    id SERIAL PRIMARY KEY,
    transcript_id UUID REFERENCES transcripts(id) ON DELETE CASCADE,
    
    -- Entity info
    text VARCHAR(500) NOT NULL,
    normalized_text VARCHAR(500), -- Canonical form
    entity_type entity_type NOT NULL,
    
    -- Position in transcript
    start_position INTEGER,
    end_position INTEGER,
    
    -- Additional info
    confidence DECIMAL(5,4),
    metadata JSONB, -- Additional entity-specific data
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_entities_transcript (transcript_id),
    INDEX idx_entities_type (entity_type),
    INDEX idx_entities_text (text),
    INDEX idx_entities_normalized (normalized_text)
);

-- Transcript versions (for collaboration)
CREATE TABLE transcript_versions (
    id SERIAL PRIMARY KEY,
    transcript_id UUID REFERENCES transcripts(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    
    -- Content snapshot
    content TEXT NOT NULL,
    summary TEXT,
    entities JSONB,
    
    -- Change tracking
    changed_by_id INTEGER REFERENCES users(id),
    change_summary TEXT,
    diff JSONB, -- Structured diff data
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(transcript_id, version_number),
    INDEX idx_versions_transcript (transcript_id, version_number DESC)
);

-- ===========================================
-- SHARING AND PERMISSIONS
-- ===========================================

-- Shared links for transcripts
CREATE TABLE shared_links (
    id SERIAL PRIMARY KEY,
    transcript_id UUID REFERENCES transcripts(id) ON DELETE CASCADE,
    
    -- Share info
    share_token VARCHAR(100) UNIQUE NOT NULL,
    created_by_id INTEGER REFERENCES users(id),
    
    -- Permissions
    permission share_permission DEFAULT 'view',
    allow_download BOOLEAN DEFAULT false,
    require_auth BOOLEAN DEFAULT false,
    
    -- Security
    password_hash VARCHAR(255),
    allowed_emails TEXT[], -- Whitelist of emails
    allowed_domains TEXT[], -- Whitelist of email domains
    
    -- Limits
    expires_at TIMESTAMP WITH TIME ZONE,
    max_views INTEGER,
    view_count INTEGER DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_shared_links_transcript (transcript_id),
    INDEX idx_shared_links_token (share_token),
    INDEX idx_shared_links_expires (expires_at)
);

-- Access logs for shared links
CREATE TABLE share_access_logs (
    id SERIAL PRIMARY KEY,
    shared_link_id INTEGER REFERENCES shared_links(id) ON DELETE CASCADE,
    
    -- Access info
    accessed_by_email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    referer TEXT,
    
    -- Actions
    action VARCHAR(50), -- view, download, comment, etc.
    
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_access_logs_link (shared_link_id),
    INDEX idx_access_logs_time (accessed_at DESC)
);

-- ===========================================
-- COLLABORATION FEATURES
-- ===========================================

-- Annotations/Comments on transcripts
CREATE TABLE annotations (
    id SERIAL PRIMARY KEY,
    transcript_id UUID REFERENCES transcripts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES annotations(id) ON DELETE CASCADE, -- For replies
    
    -- Content
    content TEXT NOT NULL,
    
    -- Position in transcript
    position_start INTEGER,
    position_end INTEGER,
    highlighted_text TEXT,
    timestamp_start DECIMAL(10,3), -- For timed comments
    timestamp_end DECIMAL(10,3),
    
    -- Status
    is_resolved BOOLEAN DEFAULT false,
    resolved_by_id INTEGER REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_annotations_transcript (transcript_id),
    INDEX idx_annotations_user (user_id),
    INDEX idx_annotations_parent (parent_id)
);

-- Mentions in annotations
CREATE TABLE mentions (
    id SERIAL PRIMARY KEY,
    annotation_id INTEGER REFERENCES annotations(id) ON DELETE CASCADE,
    mentioned_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(annotation_id, mentioned_user_id),
    INDEX idx_mentions_user (mentioned_user_id)
);

-- ===========================================
-- NOTIFICATIONS
-- ===========================================

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification info
    type notification_type NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Related entities
    related_id VARCHAR(100), -- ID of related entity
    related_type VARCHAR(50), -- Type of related entity
    link VARCHAR(500), -- Direct link to content
    
    -- Sender
    from_user_id INTEGER REFERENCES users(id),
    
    -- Status
    is_read BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional data
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_notifications_user (user_id, is_read, created_at DESC),
    INDEX idx_notifications_type (type)
);

-- ===========================================
-- ANALYTICS AND USAGE
-- ===========================================

-- Usage analytics table
CREATE TABLE usage_analytics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
    
    -- Action tracking
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    session_id UUID,
    
    -- Performance
    duration_ms INTEGER, -- For timed operations
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_analytics_user (user_id),
    INDEX idx_analytics_team (team_id),
    INDEX idx_analytics_action (action),
    INDEX idx_analytics_time (created_at DESC)
);

-- Processing queue for async jobs
CREATE TABLE processing_queue (
    id SERIAL PRIMARY KEY,
    
    -- Job info
    job_id UUID UNIQUE DEFAULT gen_random_uuid(),
    job_type VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 5, -- 1-10, higher is more important
    
    -- Related entities
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    transcript_id UUID REFERENCES transcripts(id) ON DELETE CASCADE,
    
    -- Status
    status processing_status DEFAULT 'pending',
    progress INTEGER DEFAULT 0, -- 0-100
    
    -- Input/Output
    input_data JSONB NOT NULL,
    output_data JSONB,
    error_message TEXT,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    INDEX idx_queue_status (status, priority DESC, created_at),
    INDEX idx_queue_user (user_id),
    INDEX idx_queue_job_id (job_id)
);

-- ===========================================
-- ADVANCED FEATURES
-- ===========================================

-- Tags for organization
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7), -- Hex color
    description TEXT,
    
    created_by_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Many-to-many transcript tags
CREATE TABLE transcript_tags (
    transcript_id UUID REFERENCES transcripts(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    
    PRIMARY KEY (transcript_id, tag_id)
);

-- Webhooks for integrations
CREATE TABLE webhooks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    
    -- Webhook config
    name VARCHAR(255) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    secret VARCHAR(255), -- For signing payloads
    
    -- Events to trigger on
    events TEXT[] NOT NULL,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    last_triggered TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_webhooks_user (user_id),
    INDEX idx_webhooks_team (team_id)
);

-- Export history
CREATE TABLE export_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    transcript_id UUID REFERENCES transcripts(id) ON DELETE CASCADE,
    
    -- Export details
    format export_format NOT NULL,
    options JSONB DEFAULT '{}',
    file_path VARCHAR(500),
    file_size BIGINT,
    
    -- Status
    status processing_status DEFAULT 'completed',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_export_user (user_id),
    INDEX idx_export_transcript (transcript_id)
);

-- ===========================================
-- FUNCTIONS AND TRIGGERS
-- ===========================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_transcripts_updated_at BEFORE UPDATE ON transcripts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_annotations_updated_at BEFORE UPDATE ON annotations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update team storage usage
CREATE OR REPLACE FUNCTION update_team_storage()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE teams 
        SET storage_used_mb = (
            SELECT COALESCE(SUM(file_size), 0) / 1048576.0
            FROM transcripts 
            WHERE team_id = NEW.team_id
        )
        WHERE id = NEW.team_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE teams 
        SET storage_used_mb = (
            SELECT COALESCE(SUM(file_size), 0) / 1048576.0
            FROM transcripts 
            WHERE team_id = OLD.team_id
        )
        WHERE id = OLD.team_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_team_storage_trigger
AFTER INSERT OR UPDATE OR DELETE ON transcripts
FOR EACH ROW EXECUTE FUNCTION update_team_storage();

-- Function to clean expired sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM sessions WHERE expires_at < NOW() AND is_active = true;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate user statistics
CREATE OR REPLACE FUNCTION get_user_statistics(p_user_id INTEGER)
RETURNS TABLE (
    total_transcripts BIGINT,
    total_duration_seconds NUMERIC,
    total_words BIGINT,
    avg_confidence NUMERIC,
    storage_used_mb NUMERIC,
    team_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT t.id) as total_transcripts,
        COALESCE(SUM(t.duration), 0) as total_duration_seconds,
        COALESCE(SUM(t.word_count), 0) as total_words,
        AVG(t.confidence) as avg_confidence,
        COALESCE(SUM(t.file_size), 0) / 1048576.0 as storage_used_mb,
        COUNT(DISTINCT tm.team_id) as team_count
    FROM users u
    LEFT JOIN transcripts t ON u.id = t.user_id
    LEFT JOIN team_members tm ON u.id = tm.user_id
    WHERE u.id = p_user_id
    GROUP BY u.id;
END;
$$ LANGUAGE plpgsql;

-- ===========================================
-- VIEWS
-- ===========================================

-- User dashboard view
CREATE OR REPLACE VIEW user_dashboard AS
SELECT 
    u.id,
    u.email,
    u.full_name,
    u.subscription_tier,
    u.storage_quota_mb,
    u.storage_used_mb,
    u.monthly_minutes_quota,
    u.monthly_minutes_used,
    COUNT(DISTINCT t.id) as transcript_count,
    COUNT(DISTINCT tm.team_id) as team_count,
    COUNT(DISTINCT CASE WHEN n.is_read = false THEN n.id END) as unread_notifications
FROM users u
LEFT JOIN transcripts t ON u.id = t.user_id
LEFT JOIN team_members tm ON u.id = tm.user_id
LEFT JOIN notifications n ON u.id = n.user_id
GROUP BY u.id;

-- Team analytics view
CREATE OR REPLACE VIEW team_analytics AS
SELECT 
    t.id,
    t.name,
    t.storage_quota_mb,
    t.storage_used_mb,
    t.monthly_minutes_quota,
    t.monthly_minutes_used,
    COUNT(DISTINCT tm.user_id) as member_count,
    COUNT(DISTINCT tr.id) as transcript_count,
    COUNT(DISTINCT p.id) as project_count,
    SUM(tr.duration) / 60.0 as total_minutes,
    AVG(tr.confidence) as avg_confidence
FROM teams t
LEFT JOIN team_members tm ON t.id = tm.team_id
LEFT JOIN transcripts tr ON t.id = tr.team_id
LEFT JOIN projects p ON t.id = p.team_id
GROUP BY t.id;

-- Recent activity view
CREATE OR REPLACE VIEW recent_activity AS
SELECT 
    'transcript' as activity_type,
    t.id::text as resource_id,
    t.title as resource_name,
    t.user_id,
    t.team_id,
    t.created_at as activity_time,
    'created' as action
FROM transcripts t
WHERE t.created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT 
    'annotation' as activity_type,
    a.id::text as resource_id,
    LEFT(a.content, 100) as resource_name,
    a.user_id,
    t.team_id,
    a.created_at as activity_time,
    'commented' as action
FROM annotations a
JOIN transcripts t ON a.transcript_id = t.id
WHERE a.created_at > NOW() - INTERVAL '7 days'

ORDER BY activity_time DESC;

-- ===========================================
-- INDEXES FOR PERFORMANCE
-- ===========================================

-- Additional performance indexes
CREATE INDEX idx_transcripts_user_created ON transcripts(user_id, created_at DESC);
CREATE INDEX idx_transcripts_team_created ON transcripts(team_id, created_at DESC);
CREATE INDEX idx_transcripts_public ON transcripts(is_public, created_at DESC) WHERE is_public = true;

-- Composite indexes for common queries
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, created_at DESC) 
WHERE is_read = false AND is_archived = false;

CREATE INDEX idx_processing_queue_pending ON processing_queue(priority DESC, created_at) 
WHERE status = 'pending';

-- GIN indexes for JSONB columns
CREATE INDEX idx_users_preferences ON users USING gin(preferences);
CREATE INDEX idx_transcripts_metadata ON transcripts USING gin(metadata);
CREATE INDEX idx_usage_analytics_metadata ON usage_analytics USING gin(metadata);

-- ===========================================
-- PERMISSIONS
-- ===========================================

-- Create application user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'transcription_user') THEN
        CREATE USER transcription_user WITH PASSWORD 'change_in_production';
    END IF;
END
$$;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO transcription_user;
GRANT CREATE ON SCHEMA public TO transcription_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO transcription_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO transcription_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO transcription_user;

-- ===========================================
-- INITIAL DATA
-- ===========================================

-- Insert default tags
INSERT INTO tags (name, color, description) VALUES
    ('important', '#ff0000', 'High priority content'),
    ('review', '#ffa500', 'Needs review'),
    ('final', '#00ff00', 'Finalized content'),
    ('draft', '#808080', 'Work in progress')
ON CONFLICT (name) DO NOTHING;

-- Insert default admin user (CHANGE PASSWORD IN PRODUCTION!)
INSERT INTO users (
    email, 
    username, 
    password_hash, 
    full_name, 
    role, 
    subscription_tier, 
    is_active, 
    is_verified, 
    email_verified
) VALUES (
    'admin@example.com',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeUvUFKNpvXhJpm2i', -- password: admin123
    'System Administrator',
    'admin',
    'enterprise',
    true,
    true,
    true
) ON CONFLICT (email) DO NOTHING;