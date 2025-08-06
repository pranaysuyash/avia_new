# System Architecture Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Applications                             │
├─────────────────┬─────────────────┬─────────────────┬──────────────────────┤
│   Web App       │  Desktop App    │   Mobile App    │   Developer API      │
│  (React)        │ (Electron/React)│ (React Native)  │   (REST/GraphQL)     │
└────────┬────────┴────────┬────────┴────────┬────────┴──────────┬───────────┘
         │                 │                 │                    │
         └─────────────────┴─────────────────┴────────────────────┘
                                    │
                           ┌────────▼────────┐
                           │  Load Balancer  │
                           │   (SSL/TLS)     │
                           └────────┬────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
┌────────▼────────┐       ┌────────▼────────┐       ┌────────▼────────┐
│   API Gateway   │       │   API Gateway   │       │  WebSocket GW   │
│   Instance 1    │       │   Instance 2    │       │   (Sticky)      │
└────────┬────────┘       └────────┬────────┘       └────────┬────────┘
         │                          │                          │
         └──────────────────────────┴──────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │      API Middleware Layer     │
                    ├───────────────────────────────┤
                    │ • Authentication (JWT)        │
                    │ • Quota Enforcement          │
                    │ • Rate Limiting              │
                    │ • Audit Logging              │
                    │ • Request Monitoring         │
                    └───────────────┬───────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────▼────────┐  ┌──────────────▼──────────────┐  ┌────────▼────────┐
│  Core Services │  │   Enterprise Services       │  │  Media Services │
├────────────────┤  ├─────────────────────────────┤  ├─────────────────┤
│ • Auth         │  │ • Subscription Management   │  │ • Transcription │
│ • Users        │  │ • Team Collaboration        │  │ • OCR           │
│ • Teams        │  │ • Compliance & Security     │  │ • TTS           │
│ • Transcripts  │  │ • Customer Support          │  │ • Audio Enhance │
│ • Search       │  │ • Enterprise Sales          │  │ • NER           │
└────────┬───────┘  │ • Marketing & Growth        │  └────────┬────────┘
         │          │ • API Platform               │           │
         │          │ • AI Customization           │           │
         │          └──────────────┬───────────────┘           │
         │                         │                           │
         └─────────────────────────┴───────────────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │    Data Access Layer        │
                    ├──────────────────────────────┤
                    │ • ORM (SQLAlchemy)          │
                    │ • Query Optimization        │
                    │ • Connection Pooling        │
                    └──────────────┬──────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐       ┌────────▼────────┐       ┌─────────▼────────┐
│  PostgreSQL    │       │     Redis        │       │   S3 Storage     │
│   Primary      │       │    Cluster       │       │  (Media Files)   │
├────────────────┤       ├─────────────────┤       ├──────────────────┤
│ • Users        │       │ • Session Cache │       │ • Audio Files    │
│ • Transcripts  │       │ • Rate Limits   │       │ • Video Files    │
│ • Teams        │       │ • Usage Quotas  │       │ • Transcripts    │
│ • Audit Logs   │       │ • Feature Flags │       │ • Exports        │
│ • Subscriptions│       │ • Temp Data     │       │ • Archives       │
└────────┬───────┘       └─────────────────┘       └──────────────────┘
         │
┌────────▼────────┐
│  PostgreSQL     │
│  Read Replicas  │
└─────────────────┘
```

## Detailed Component Breakdown

### 1. Client Layer
```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
├──────────────┬──────────────┬──────────────┬───────────────┤
│  Web App     │ Desktop App  │ Mobile App   │ Developer API │
├──────────────┼──────────────┼──────────────┼───────────────┤
│ • React 18   │ • Electron   │ • React      │ • REST API    │
│ • TypeScript │ • React 18   │   Native     │ • GraphQL     │
│ • Redux      │ • TypeScript │ • TypeScript │ • WebSockets  │
│ • Material UI│ • IPC Bridge │ • Native     │ • SDKs        │
│              │              │   Base       │               │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

### 2. API Gateway & Middleware
```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                       │
├─────────────────────────────────────────────────────────────┤
│ FastAPI Application                                         │
│ ├─ Middleware Pipeline                                      │
│ │  ├─ CORS Handler                                         │
│ │  ├─ Authentication (JWT + API Keys)                      │
│ │  ├─ Quota Enforcement (402 Payment Required)             │
│ │  ├─ Rate Limiting (Redis-backed)                         │
│ │  ├─ Audit Logging (Risk Scoring)                         │
│ │  ├─ Request Monitoring (OpenTelemetry)                   │
│ │  └─ Error Handling                                       │
│ │                                                           │
│ └─ Route Handlers                                          │
│    ├─ /api/v1/auth/*                                       │
│    ├─ /api/v1/transcripts/*                                │
│    ├─ /api/v1/media/*                                      │
│    ├─ /api/v1/teams/*                                      │
│    └─ /api/v1/enterprise/*                                 │
└─────────────────────────────────────────────────────────────┘
```

### 3. Service Layer Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
├─────────────────────────┬───────────────────────────────────┤
│   Core Services         │   Enterprise Services             │
├─────────────────────────┼───────────────────────────────────┤
│ AuthService             │ SubscriptionService               │
│ ├─ Login/Logout         │ ├─ Plan Management                │
│ ├─ Token Management     │ ├─ Usage Tracking                 │
│ └─ Password Reset       │ └─ Billing Integration            │
│                         │                                   │
│ UserService             │ CollaborationService              │
│ ├─ Profile Management   │ ├─ Real-time Updates              │
│ ├─ Preferences          │ ├─ Comments/Mentions              │
│ └─ Account Settings     │ └─ Version Control                │
│                         │                                   │
│ TranscriptionService    │ ComplianceService                 │
│ ├─ Audio Processing     │ ├─ Audit Trail                    │
│ ├─ Queue Management     │ ├─ Data Retention                 │
│ └─ Result Storage       │ └─ Export/Purge                   │
└─────────────────────────┴───────────────────────────────────┘
```

### 4. Data Layer
```
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
├──────────────┬──────────────┬───────────────────────────────┤
│ PostgreSQL   │ Redis        │ S3 Object Storage             │
├──────────────┼──────────────┼───────────────────────────────┤
│ Tables:      │ Keys:        │ Buckets:                      │
│ • users      │ • sessions:* │ • transcription-media/        │
│ • teams      │ • quota:*    │   ├─ audio/                   │
│ • transcripts│ • ratelimit:*│   ├─ video/                   │
│ • audit_logs │ • cache:*    │   └─ processed/               │
│ • usage_logs │ • locks:*    │ • transcription-exports/       │
│ • subscript. │              │ • transcription-archives/      │
│ • retention  │              │                               │
└──────────────┴──────────────┴───────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
├─────────────────────────────────────────────────────────────┤
│ 1. Network Security                                         │
│    • SSL/TLS encryption (HTTPS only)                        │
│    • VPC with private subnets                               │
│    • Web Application Firewall (WAF)                         │
│                                                             │
│ 2. Application Security                                     │
│    • JWT tokens with expiration                             │
│    • API key authentication for developers                  │
│    • Role-Based Access Control (RBAC)                       │
│    • Input validation and sanitization                      │
│                                                             │
│ 3. Data Security                                            │
│    • Encryption at rest (AES-256)                           │
│    • Encryption in transit (TLS 1.3)                        │
│    • Sensitive data redaction in logs                       │
│    • Automated data retention/deletion                      │
│                                                             │
│ 4. Monitoring & Compliance                                  │
│    • Audit logging with risk scoring                        │
│    • Real-time security alerts                              │
│    • Compliance reporting (GDPR, SOC2)                      │
│    • Automated vulnerability scanning                       │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Production Deployment                        │
├─────────────────────────────────────────────────────────────┤
│ Kubernetes Cluster (Multi-AZ)                               │
│ ├─ API Pods (3+ replicas)                                  │
│ ├─ WebSocket Pods (2+ replicas, sticky sessions)           │
│ ├─ Background Worker Pods                                   │
│ └─ Cron Job Pods (data retention, usage reset)             │
│                                                             │
│ External Services                                           │
│ ├─ CloudFront CDN                                          │
│ ├─ Route 53 DNS                                            │
│ ├─ SES Email Service                                       │
│ └─ CloudWatch Monitoring                                    │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow Example: Transcription Request

```
1. Client Upload
   Web App ──────► API Gateway ──────► Auth Check ──────► Quota Check
                                                              │
2. Processing                                                 ▼
   Media Service ◄────── Queue ◄────── Store in S3 ◄────── Valid
        │
        ▼
   Transcription ──────► AI Model ──────► Post-Process ──────► Store Result
                                                                    │
3. Notification                                                     ▼
   WebSocket ◄────── Event ◄────── Update DB ◄────── Audit Log ◄───┘
        │
        ▼
   Client Update
```

This architecture provides:
- **Scalability**: Horizontal scaling at each layer
- **Reliability**: Redundancy and failover capabilities
- **Security**: Multiple layers of protection
- **Performance**: Caching and optimization throughout
- **Compliance**: Audit trails and data governance