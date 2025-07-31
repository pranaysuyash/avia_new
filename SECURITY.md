# Security Guide

## Overview

This document outlines security best practices for deploying and operating the Audio/Video Transcription and Entity Extraction App in production environments.

## Table of Contents

1. [API Key Management](#api-key-management)
2. [Container Security](#container-security)
3. [Network Security](#network-security)
4. [Data Protection](#data-protection)
5. [Access Control](#access-control)
6. [Monitoring and Auditing](#monitoring-and-auditing)
7. [Incident Response](#incident-response)

## API Key Management

### Best Practices

1. **Environment Variables Only**
   ```bash
   # ✅ Correct: Use environment variables
   OPENAI_API_KEY=sk-your-key-here
   ELEVENLABS_API_KEY=your-key-here
   
   # ❌ Never: Hardcode in source code
   api_key = "sk-your-key-here"  # DON'T DO THIS
   ```

2. **Docker Secrets (Recommended)**
   ```bash
   # Create secrets
   echo "sk-your-openai-key" | docker secret create openai_api_key -
   echo "your-elevenlabs-key" | docker secret create elevenlabs_api_key -
   
   # Use in docker-compose.yml
   services:
     transcription-app:
       secrets:
         - openai_api_key
         - elevenlabs_api_key
   
   secrets:
     openai_api_key:
       external: true
     elevenlabs_api_key:
       external: true
   ```

3. **Key Rotation Strategy**
   ```bash
   # Regular rotation (monthly recommended)
   # 1. Generate new API key
   # 2. Update secret
   docker secret create openai_api_key_v2 new_key.txt
   
   # 3. Update service
   docker service update --secret-rm openai_api_key \
                         --secret-add openai_api_key_v2 \
                         transcription-app
   
   # 4. Remove old secret
   docker secret rm openai_api_key
   ```

4. **Access Restrictions**
   ```bash
   # Limit API key permissions where possible
   # OpenAI: Use project-specific keys
   # ElevenLabs: Set usage limits
   
   # Monitor API usage
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/usage
   ```

### Key Storage Security

1. **File Permissions**
   ```bash
   # Secure .env file
   chmod 600 .env
   chown root:root .env
   
   # Verify permissions
   ls -la .env
   # Should show: -rw------- 1 root root
   ```

2. **Backup Security**
   ```bash
   # Encrypt backups containing keys
   gpg --symmetric --cipher-algo AES256 .env
   
   # Store encrypted version only
   rm .env
   mv .env.gpg secure_location/
   ```

3. **Key Validation**
   ```python
   # Implement key validation in application
   def validate_api_key(key: str, service: str) -> bool:
       """Validate API key format and test connectivity"""
       if service == "openai":
           return key.startswith("sk-") and len(key) > 20
       elif service == "elevenlabs":
           return len(key) > 10 and key.isalnum()
       return False
   ```

## Container Security

### Image Security

1. **Base Image Selection**
   ```dockerfile
   # ✅ Use official, minimal images
   FROM python:3.11-slim
   
   # ❌ Avoid full OS images
   FROM ubuntu:latest  # Too large, more attack surface
   ```

2. **Security Updates**
   ```dockerfile
   # Keep base image updated
   RUN apt-get update && apt-get upgrade -y \
       && rm -rf /var/lib/apt/lists/*
   ```

3. **Vulnerability Scanning**
   ```bash
   # Scan images regularly
   docker scan transcription-app
   
   # Use tools like Trivy
   trivy image transcription-app
   ```

### Runtime Security

1. **Non-Root User**
   ```dockerfile
   # Create and use non-root user
   RUN groupadd -r appuser && useradd -r -g appuser appuser
   USER appuser
   ```

2. **Read-Only Filesystem**
   ```yaml
   # docker-compose.yml
   services:
     transcription-app:
       read_only: true
       tmpfs:
         - /tmp:noexec,nosuid,size=100m
         - /app/temp:noexec,nosuid,size=500m
   ```

3. **Security Options**
   ```yaml
   services:
     transcription-app:
       security_opt:
         - no-new-privileges:true
         - seccomp:unconfined  # Only if needed
       cap_drop:
         - ALL
       cap_add:
         - CHOWN  # Only if needed
   ```

### Resource Limits

```yaml
services:
  transcription-app:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
          pids: 100
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Network Security

### Firewall Configuration

1. **Host Firewall**
   ```bash
   # UFW configuration
   ufw default deny incoming
   ufw default allow outgoing
   
   # Allow only necessary ports
   ufw allow 22/tcp    # SSH
   ufw allow 80/tcp    # HTTP
   ufw allow 443/tcp   # HTTPS
   
   # Block direct application access
   ufw deny 8501/tcp
   
   ufw enable
   ```

2. **Docker Network Security**
   ```yaml
   # docker-compose.yml
   networks:
     default:
       driver: bridge
       ipam:
         config:
           - subnet: 172.20.0.0/16
       driver_opts:
         com.docker.network.bridge.enable_icc: "false"
   ```

### Reverse Proxy Security

1. **Nginx Security Headers**
   ```nginx
   # Security headers
   add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
   add_header X-Frame-Options DENY always;
   add_header X-Content-Type-Options nosniff always;
   add_header X-XSS-Protection "1; mode=block" always;
   add_header Referrer-Policy "strict-origin-when-cross-origin" always;
   ```

2. **Rate Limiting**
   ```nginx
   # Rate limiting zones
   limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
   limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/m;
   
   # Apply limits
   location / {
       limit_req zone=api burst=20 nodelay;
   }
   ```

3. **IP Whitelisting**
   ```nginx
   # Restrict admin endpoints
   location /admin {
       allow 192.168.1.0/24;  # Internal network
       allow 10.0.0.0/8;      # VPN network
       deny all;
   }
   ```

### SSL/TLS Configuration

1. **Certificate Management**
   ```bash
   # Let's Encrypt (automated)
   certbot --nginx -d your-domain.com
   
   # Manual certificate
   openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
     -keyout server.key -out server.crt
   ```

2. **SSL Configuration**
   ```nginx
   # Modern SSL configuration
   ssl_protocols TLSv1.2 TLSv1.3;
   ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
   ssl_prefer_server_ciphers off;
   ssl_session_cache shared:SSL:10m;
   ssl_session_timeout 10m;
   ```

## Data Protection

### File Security

1. **Temporary File Management**
   ```python
   # Secure temp file creation
   import tempfile
   import os
   
   def create_secure_temp_file():
       fd, path = tempfile.mkstemp(prefix='secure_', suffix='.tmp')
       os.chmod(path, 0o600)  # Owner read/write only
       return fd, path
   ```

2. **File Cleanup**
   ```python
   # Automatic cleanup
   import atexit
   import shutil
   
   def cleanup_temp_files():
       temp_dir = "/app/temp"
       if os.path.exists(temp_dir):
           shutil.rmtree(temp_dir)
           os.makedirs(temp_dir, mode=0o700)
   
   atexit.register(cleanup_temp_files)
   ```

3. **Data Encryption at Rest**
   ```bash
   # Encrypt sensitive volumes
   docker volume create --driver local \
     --opt type=tmpfs \
     --opt device=tmpfs \
     --opt o=size=1g,uid=1000,gid=1000,mode=0700 \
     encrypted_temp
   ```

### Data Retention

1. **Automatic Cleanup Policy**
   ```python
   # config.py
   DATA_RETENTION_HOURS = 24  # Delete files after 24 hours
   MAX_TEMP_FILES = 100       # Maximum temp files
   
   def cleanup_old_files():
       """Remove files older than retention period"""
       import time
       import glob
       
       cutoff_time = time.time() - (DATA_RETENTION_HOURS * 3600)
       temp_files = glob.glob("/app/temp/*")
       
       for file_path in temp_files:
           if os.path.getmtime(file_path) < cutoff_time:
               os.remove(file_path)
   ```

2. **Secure Deletion**
   ```python
   def secure_delete(file_path: str):
       """Securely delete file by overwriting"""
       if os.path.exists(file_path):
           file_size = os.path.getsize(file_path)
           with open(file_path, "r+b") as file:
               file.write(os.urandom(file_size))
               file.flush()
               os.fsync(file.fileno())
           os.remove(file_path)
   ```

## Access Control

### Authentication

1. **Admin Panel Security**
   ```python
   # Strong password requirements
   import secrets
   import hashlib
   
   def generate_secure_password():
       return secrets.token_urlsafe(32)
   
   def hash_password(password: str) -> str:
       salt = secrets.token_hex(16)
       pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                     password.encode('utf-8'), 
                                     salt.encode('utf-8'), 
                                     100000)
       return salt + pwdhash.hex()
   ```

2. **Session Management**
   ```python
   # Secure session configuration
   SESSION_TIMEOUT = 3600  # 1 hour
   SESSION_COOKIE_SECURE = True
   SESSION_COOKIE_HTTPONLY = True
   SESSION_COOKIE_SAMESITE = 'Strict'
   ```

### Authorization

1. **Role-Based Access**
   ```python
   class UserRole:
       VIEWER = "viewer"
       USER = "user"
       ADMIN = "admin"
   
   def check_permission(user_role: str, required_role: str) -> bool:
       role_hierarchy = {
           UserRole.VIEWER: 0,
           UserRole.USER: 1,
           UserRole.ADMIN: 2
       }
       return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)
   ```

2. **API Access Control**
   ```python
   def require_api_key(func):
       def wrapper(*args, **kwargs):
           api_key = request.headers.get('X-API-Key')
           if not validate_api_key(api_key):
               return {"error": "Invalid API key"}, 401
           return func(*args, **kwargs)
       return wrapper
   ```

## Monitoring and Auditing

### Security Logging

1. **Audit Trail**
   ```python
   # security_logger.py
   import logging
   
   security_logger = logging.getLogger('security')
   
   def log_security_event(event_type: str, user_id: str = None, details: dict = None):
       """Log security events for audit trail"""
       log_data = {
           'event_type': event_type,
           'user_id': user_id,
           'timestamp': datetime.utcnow().isoformat(),
           'ip_address': request.remote_addr,
           'user_agent': request.headers.get('User-Agent'),
           'details': details or {}
       }
       security_logger.info(f"SECURITY_EVENT: {event_type}", extra=log_data)
   ```

2. **Failed Login Monitoring**
   ```python
   failed_attempts = {}
   
   def track_failed_login(ip_address: str):
       if ip_address not in failed_attempts:
           failed_attempts[ip_address] = 0
       failed_attempts[ip_address] += 1
       
       if failed_attempts[ip_address] > 5:
           log_security_event("BRUTE_FORCE_ATTEMPT", details={"ip": ip_address})
           # Implement IP blocking
   ```

### Vulnerability Monitoring

1. **Dependency Scanning**
   ```bash
   # Regular dependency audits
   pip-audit
   safety check
   
   # Update dependencies
   pip-review --auto
   ```

2. **Container Scanning**
   ```bash
   # Automated scanning in CI/CD
   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
     aquasec/trivy image transcription-app
   ```

### Intrusion Detection

1. **Log Analysis**
   ```bash
   # Monitor for suspicious patterns
   grep "SECURITY_EVENT" /app/logs/app_security.log | \
     grep "BRUTE_FORCE_ATTEMPT" | \
     tail -20
   ```

2. **Automated Alerts**
   ```python
   def check_security_alerts():
       """Check for security incidents and send alerts"""
       # Check failed login attempts
       # Check unusual API usage patterns
       # Check file access patterns
       # Send alerts via email/Slack
   ```

## Incident Response

### Preparation

1. **Incident Response Plan**
   - Define roles and responsibilities
   - Create communication channels
   - Prepare isolation procedures
   - Document recovery procedures

2. **Emergency Contacts**
   ```yaml
   # incident_contacts.yml
   security_team:
     - name: "Security Lead"
       email: "security@company.com"
       phone: "+1-555-0123"
   
   infrastructure_team:
     - name: "DevOps Lead"
       email: "devops@company.com"
       phone: "+1-555-0124"
   ```

### Response Procedures

1. **Immediate Response**
   ```bash
   # Isolate compromised container
   docker stop transcription-app
   
   # Preserve evidence
   docker commit transcription-app evidence-$(date +%Y%m%d-%H%M%S)
   
   # Check logs
   docker logs transcription-app > incident-logs.txt
   ```

2. **Investigation**
   ```bash
   # Analyze security logs
   grep -E "(SECURITY_EVENT|ERROR|CRITICAL)" /app/logs/app_security.log
   
   # Check system integrity
   docker diff transcription-app
   
   # Network analysis
   netstat -tulpn
   ```

3. **Recovery**
   ```bash
   # Clean deployment
   docker-compose down
   docker system prune -a
   
   # Restore from clean backup
   docker-compose up -d --build
   
   # Verify integrity
   curl http://localhost:8501/health-detailed
   ```

### Post-Incident

1. **Documentation**
   - Timeline of events
   - Root cause analysis
   - Impact assessment
   - Lessons learned

2. **Improvements**
   - Update security policies
   - Enhance monitoring
   - Improve response procedures
   - Conduct security training

## Security Checklist

### Pre-Deployment

- [ ] API keys stored securely (not in code)
- [ ] Strong admin passwords configured
- [ ] SSL certificates installed and configured
- [ ] Firewall rules configured
- [ ] Container security options enabled
- [ ] Vulnerability scanning completed
- [ ] Security headers configured
- [ ] Rate limiting implemented
- [ ] Logging and monitoring configured
- [ ] Backup and recovery procedures tested

### Post-Deployment

- [ ] Security monitoring active
- [ ] Log analysis automated
- [ ] Incident response plan activated
- [ ] Regular security updates scheduled
- [ ] Access controls verified
- [ ] Data retention policies enforced
- [ ] Security training completed
- [ ] Penetration testing scheduled

### Ongoing Maintenance

- [ ] Monthly security updates
- [ ] Quarterly vulnerability assessments
- [ ] Annual penetration testing
- [ ] Regular backup testing
- [ ] Security policy reviews
- [ ] Incident response drills
- [ ] Security awareness training
- [ ] Compliance audits

## Compliance Considerations

### Data Privacy

- **GDPR**: Implement data subject rights, consent management
- **CCPA**: Provide data deletion and access rights
- **HIPAA**: If processing healthcare data, implement additional controls

### Industry Standards

- **SOC 2**: Implement security, availability, and confidentiality controls
- **ISO 27001**: Establish information security management system
- **NIST**: Follow cybersecurity framework guidelines

### Documentation Requirements

- Security policies and procedures
- Risk assessments and mitigation plans
- Incident response documentation
- Audit logs and compliance reports

---

For additional security guidance or to report security issues, please contact the security team or create a confidential issue in the project repository.