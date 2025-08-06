# Enterprise Features Quick Start Guide

## 1. Starting the System

```bash
# Start all services
./start_with_api.sh

# Or start individually:
# Backend API
cd /Users/pranay/Projects/LLM/video/ner
python api/app.py

# Desktop App (in new terminal)
cd desktop_app
npm run dev

# Mobile App (in new terminal) 
cd mobile
npm run ios  # or npm run android
```

## 2. Initial Setup

### Initialize Enterprise Features

```bash
# 1. Create admin user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@company.com",
    "password": "secure_password",
    "role": "admin"
  }'

# 2. Login to get token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "secure_password"
  }' | jq -r '.access_token'

# Save the token
export ADMIN_TOKEN="<token-from-above>"

# 3. Initialize retention policies
curl -X POST http://localhost:8000/api/v1/data-retention/initialize \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# 4. Create subscription plans (if not already done)
curl -X POST http://localhost:8000/api/v1/subscriptions/initialize-plans \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## 3. Testing Quota Enforcement

### Create Test User with Limited Plan

```bash
# Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "test123"
  }'

# Admin assigns basic plan with limits
curl -X PUT http://localhost:8000/api/v1/users/testuser/subscription \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "basic",
    "quotas": {
      "transcripts": 10,
      "minutes": 60,
      "storage_gb": 1,
      "api_calls": 100
    }
  }'
```

### Test Quota Limits

```bash
# Get test user token
TEST_TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123"}' | jq -r '.access_token')

# Make API calls until quota exceeded
for i in {1..101}; do
  echo "Call $i:"
  curl -X POST http://localhost:8000/api/v1/audio/enhance/quality \
    -H "Authorization: Bearer $TEST_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"audio_data": "test", "format": "wav"}'
done

# Should see 402 Payment Required after 100 calls
```

## 4. Monitoring Features

### View Audit Logs

```bash
# Get recent audit logs
curl http://localhost:8000/api/v1/audit/logs?limit=10 \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# Get high-risk actions only
curl http://localhost:8000/api/v1/audit/logs?min_risk_score=8 \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# Export audit logs
curl http://localhost:8000/api/v1/audit/logs/export?format=csv \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -o audit_logs.csv
```

### Check Usage Dashboard

```bash
# User checks their usage
curl http://localhost:8000/api/v1/usage/dashboard \
  -H "Authorization: Bearer $TEST_TOKEN" | jq

# Response shows:
# {
#   "current_usage": {
#     "transcripts": 5,
#     "minutes": 23.5,
#     "storage_gb": 0.12,
#     "api_calls": 47
#   },
#   "limits": {
#     "transcripts": 10,
#     "minutes": 60,
#     "storage_gb": 1,
#     "api_calls": 100
#   },
#   "alerts": [
#     {
#       "type": "warning",
#       "message": "You have used 80% of your API calls quota"
#     }
#   ]
# }
```

## 5. Data Retention Management

### View Retention Policies

```bash
# Get all policies
curl http://localhost:8000/api/v1/data-retention/policies \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# Check expired data
curl http://localhost:8000/api/v1/data-retention/policies/temp_files/expired \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# Run manual cleanup
curl -X POST http://localhost:8000/api/v1/data-retention/cleanup/manual \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data_type": "temp_files"}'
```

## 6. Frontend Usage Tracking

### Desktop App
1. Login with test user credentials
2. Look for usage widget in the header/sidebar
3. Try actions that consume quota
4. See real-time updates and modal when quota exceeded

### Mobile App
1. Login with test user credentials
2. Check usage in profile/settings
3. Attempt actions beyond quota
4. See quota exceeded modal with upgrade prompt

## 7. Common Scenarios

### User Hits Quota Limit
1. User makes API call
2. Gets 402 Payment Required response
3. Frontend shows quota exceeded modal
4. User clicks "Upgrade Plan"
5. Redirected to subscription management

### Admin Reviews Security
1. Admin accesses audit logs
2. Filters for high-risk actions
3. Exports report for compliance
4. Reviews user activity patterns

### Automated Cleanup
1. Cron job triggers `/api/v1/data-retention/cleanup/automated`
2. System processes each auto-delete policy
3. Old data archived then deleted
4. Job results logged for audit

## 8. Troubleshooting

### Quota Not Enforcing
- Check user has subscription assigned
- Verify quota middleware is active
- Look for quota decorator on endpoint

### Audit Logs Missing
- Ensure audit middleware is enabled
- Check database migrations completed
- Verify audit_logs table exists

### Retention Jobs Failing
- Check retention policies are initialized
- Verify database permissions
- Review job error messages in logs

## 9. Run Full Test Suite

```bash
# Run the comprehensive test
python test_enterprise_features.py

# Or run individual API tests
python test_api_endpoints.py
```

## Next Steps

1. Configure production quotas
2. Set up monitoring alerts
3. Schedule retention jobs
4. Customize audit risk scores
5. Implement usage analytics dashboards