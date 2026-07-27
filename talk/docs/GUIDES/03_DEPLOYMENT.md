# 🚀 Deployment Guide

**For:** DevOps/Release engineers  
**Time:** 15 minutes (first time), 5 min (subsequent)

---

## Prerequisites

- AWS account with EC2 + RDS access
- Docker & Docker Compose
- GitHub credentials
- Access to production database

---

## Pre-Deployment Checklist

**1 day before release:**

```bash
# All tests pass
docker exec talk-app python manage.py test
→ Coverage >80%

# No pending migrations
docker exec talk-app python manage.py showmigrations
→ All applied

# Database backup created
docker exec talk-db pg_dump -U user talk > backup_$(date +%s).sql

# Performance baseline met
→ Page load <2s
→ API response <100ms
→ Video streaming working

# Code review approved
→ All PRs merged to main
→ CI/CD pipeline passing
```

---

## Staging Deployment

### 1. Deploy to Staging

```bash
# Pull latest
git pull origin main

# Build Docker image
docker build -t talk:staging .

# Deploy to staging server
ssh ubuntu@staging.talk.io
docker pull talk:staging
docker-compose -f docker-compose.staging.yml up -d
```

### 2. Run Smoke Tests

```bash
# Test API endpoints
curl https://staging.talk.io/api/courses/
curl https://staging.talk.io/api/users/

# Test console login
→ Visit https://staging.talk.io/console/
→ Login with test account

# Test student portal
→ Visit https://staging.talk.io/
→ Browse courses
```

### 3. Verify Data

```bash
# Check user counts
docker exec talk-db psql -U user talk -c "SELECT COUNT(*) FROM accounts_user;"

# Check recent errors
docker-compose logs app | grep ERROR
```

---

## Production Deployment (Blue-Green)

### 1. Deploy to Production (Green)

```bash
# SSH into production
ssh ubuntu@talk.io

# Deploy to green environment
docker pull talk:latest
docker-compose -f docker-compose.green.yml up -d

# Wait 2 minutes for startup
sleep 120

# Run smoke tests
curl https://green.talk.io/api/health/
```

### 2. Switch Traffic (Blue → Green)

```bash
# Update load balancer
aws elb modify-load-balancer-attributes \
  --load-balancer-name talk-lb \
  --load-balancer-attributes "{\"CrossZoneLoadBalancing\":{\"Enabled\":true}}"

# Verify traffic switched
→ Monitor: Real User Monitoring
→ Check error rates: <0.5%
→ Check response times: <100ms
```

### 3. Monitor for 1 Hour

```bash
# Monitor error rate
watch 'docker-compose logs --tail 100 app | grep ERROR | wc -l'

# Monitor response times
docker-compose logs app | grep "request_time"

# Monitor database
docker exec talk-db psql -U user talk -c "SELECT * FROM pg_stat_statements LIMIT 5;"
```

---

## Rollback Procedure

If something goes wrong:

### Immediate Rollback

```bash
# Switch back to blue
aws elb modify-load-balancer-attributes ...

# Scale down green
docker-compose -f docker-compose.green.yml down

# Verify blue is stable
curl https://talk.io/api/health/
```

### Database Rollback

```bash
# If database was changed
docker exec talk-db psql -U user talk < backup_timestamp.sql

# Verify restore
docker exec talk-db psql -U user talk -c "SELECT COUNT(*) FROM accounts_user;"
```

---

## Database Migrations

### Before Deploying New Code

```bash
# Test migrations on staging
docker exec talk-staging python manage.py migrate

# Verify data integrity
docker exec talk-staging python manage.py check

# If migration fails, rollback
docker exec talk-db psql -U user talk < backup.sql
```

---

## Post-Deployment Tasks

### 1. Documentation

```bash
# Update EXECUTION_PLAN.md
echo "## Version 2.1 Deployed
- Date: $(date)
- Changes: #001, #002, #003
- Database: Migrated
- Status: Healthy" >> docs/EXECUTION_PLAN.md
```

### 2. Announce Release

```bash
# Slack notification
curl -X POST webhook.slack.com \
  -d '{"text":"🚀 Talk v2.1 deployed to production"}'
```

### 3. Monitor Metrics

```bash
# Check real user monitoring
→ Datadog dashboard
→ Google Analytics
→ Custom metrics

# Expected:
→ Error rate <0.5%
→ Page load <2s
→ 99.9% uptime
```

---

## Environment Variables

**Production:**
```
DEBUG=False
SECRET_KEY=prod-secret-key
DATABASE_URL=postgresql://user:pass@rds.amazonaws.com/talk
ALLOWED_HOSTS=talk.io,www.talk.io
SENTRY_DSN=https://...
```

**Staging:**
```
DEBUG=True
DATABASE_URL=postgresql://user:pass@staging-rds/talk
ALLOWED_HOSTS=staging.talk.io
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Database connection timeout | Restart RDS connection pool |
| Disk space full | Clean old logs: `docker exec app rm /logs/*.old` |
| Memory leak | Restart container: `docker-compose restart app` |
| SSL certificate expired | Renew via Let's Encrypt |

---

## Useful Commands

```bash
# View deployment logs
docker-compose logs -f app

# Restart application
docker-compose restart app

# Database backup
docker exec talk-db pg_dump -U user talk > backup.sql

# Database restore
docker exec -i talk-db psql -U user talk < backup.sql

# Check disk space
docker exec talk-db df -h

# View database size
docker exec talk-db psql -U user talk -c "\l+"
```

---

## Rollback Plan

**If production is broken:**

1. Switch to blue environment
2. Scale down green
3. Monitor error rates (should drop immediately)
4. If database issue: restore from backup
5. Notify team in Slack

**Time to stable:** <5 minutes

---

**Next:** See `REFERENCES/` for technical details
