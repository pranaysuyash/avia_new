# Database Setup and Migration Guide

## Overview

This directory contains the database schema and migration tools for the Audio/Video Transcription Platform. The application supports both SQLite (for development) and PostgreSQL (for production).

## Files

- `models.py` - SQLAlchemy ORM models
- `schema_comprehensive.sql` - Complete PostgreSQL schema with all tables, indexes, and functions
- `init.sql` - Basic PostgreSQL initialization script (legacy)
- `README.md` - This file

## PostgreSQL Setup

### 1. Install PostgreSQL

#### macOS:
```bash
brew install postgresql
brew services start postgresql
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### Using Docker:
```bash
docker run --name postgres-transcription \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -e POSTGRES_DB=ner_transcription_db \
  -p 5432:5432 \
  -d postgres:15
```

### 2. Configure Environment

Copy the example environment file and update with your database credentials:

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL settings:
```env
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ner_transcription_db
POSTGRES_USER=transcription_user
POSTGRES_PASSWORD=your-secure-password-here

# Or use a single DATABASE_URL
DATABASE_URL=postgresql://transcription_user:password@localhost:5432/ner_transcription_db
```

### 3. Run Setup Script

The easiest way to set up the database is using our setup script:

```bash
python setup_postgres.py
```

This script will:
1. Create the database and user
2. Set up required extensions
3. Run the comprehensive schema
4. Initialize Alembic migrations

### 4. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create database and user
CREATE DATABASE ner_transcription_db;
CREATE USER transcription_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE ner_transcription_db TO transcription_user;
\q

# Run the schema
psql -U transcription_user -d ner_transcription_db -f database/schema_comprehensive.sql
```

## Database Schema

### Core Tables

1. **users** - User accounts and authentication
2. **sessions** - JWT session management
3. **api_keys** - API key authentication

### Transcription Tables

1. **transcripts** - Main transcription records
2. **speaker_segments** - Speaker diarization results
3. **entities** - Named entity recognition results
4. **transcript_versions** - Version history

### Collaboration Tables

1. **teams** - Team workspaces
2. **team_members** - Team membership
3. **projects** - Projects within teams
4. **annotations** - Comments and annotations
5. **shared_links** - Shareable transcript links

### Analytics Tables

1. **usage_analytics** - User activity tracking
2. **processing_queue** - Async job queue
3. **notifications** - User notifications

### Features

- UUID primary keys for transcripts
- Full-text search with PostgreSQL
- JSONB columns for flexible metadata
- Comprehensive indexes for performance
- Row-level security ready
- Audit triggers for important tables

## Migrations with Alembic

### Initial Setup

```bash
# Install Alembic
pip install alembic psycopg2-binary

# Initialize Alembic (already done)
alembic init migrations

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Run migrations
alembic upgrade head
```

### Creating New Migrations

```bash
# After modifying models.py
alembic revision --autogenerate -m "Add new feature"

# Review the generated migration
# Edit migrations/versions/xxx_add_new_feature.py if needed

# Apply migration
alembic upgrade head
```

### Migration Commands

```bash
# Check current version
alembic current

# Show migration history
alembic history

# Upgrade to specific revision
alembic upgrade <revision>

# Downgrade one revision
alembic downgrade -1

# Generate SQL for offline migration
alembic upgrade head --sql > migration.sql
```

## Testing Database Connection

```bash
# Test connection
python test_postgres_connection.py

# Run database tests
pytest tests/test_database.py
```

## Performance Optimization

### Indexes

The schema includes indexes for:
- Primary keys (automatic)
- Foreign keys
- Frequently queried columns
- Full-text search
- JSONB data

### Connection Pooling

Configure in your application:
```python
# In db_config/database_config.py
'pool_size': 10,
'max_overflow': 20,
'pool_timeout': 30,
'pool_recycle': 3600
```

### Maintenance

```sql
-- Analyze tables for query optimization
ANALYZE;

-- Vacuum to reclaim space
VACUUM ANALYZE;

-- Reindex for performance
REINDEX DATABASE ner_transcription_db;
```

## Backup and Restore

### Backup

```bash
# Full database backup
pg_dump -U transcription_user -d ner_transcription_db > backup.sql

# Compressed backup
pg_dump -U transcription_user -d ner_transcription_db -Fc > backup.dump

# Backup specific tables
pg_dump -U transcription_user -d ner_transcription_db -t transcripts -t users > partial_backup.sql
```

### Restore

```bash
# Restore from SQL
psql -U transcription_user -d ner_transcription_db < backup.sql

# Restore from compressed dump
pg_restore -U transcription_user -d ner_transcription_db backup.dump
```

## Troubleshooting

### Common Issues

1. **Connection refused**
   - Check if PostgreSQL is running: `pg_isready`
   - Verify port: `sudo lsof -i :5432`

2. **Authentication failed**
   - Check pg_hba.conf for authentication method
   - Verify username and password

3. **Database does not exist**
   - Run: `python setup_postgres.py`

4. **Permission denied**
   - Grant permissions: `GRANT ALL ON ALL TABLES IN SCHEMA public TO transcription_user;`

### Logs

- PostgreSQL logs: `/var/log/postgresql/` or `pg_log/`
- Application logs: Check `logs/` directory

## Production Considerations

1. **Security**
   - Use strong passwords
   - Enable SSL connections
   - Restrict network access
   - Regular security updates

2. **Performance**
   - Monitor slow queries
   - Regular VACUUM and ANALYZE
   - Proper indexing strategy
   - Connection pooling

3. **Backup**
   - Automated daily backups
   - Test restore procedures
   - Off-site backup storage

4. **Monitoring**
   - Set up PostgreSQL monitoring
   - Track database size
   - Monitor connection count
   - Alert on errors

## Docker Deployment

For production, use Docker Compose:

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f db

# Connect to database
docker-compose exec db psql -U transcription_user -d ner_transcription_db
```