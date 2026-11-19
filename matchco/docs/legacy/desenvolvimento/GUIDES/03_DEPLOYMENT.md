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
docker exec matchco-app python manage.py test
→ Coverage >80%

# No pending migrations
docker exec matchco-app python manage.py showmigrations
→ All applied

# Database backup created
docker exec matchco-db pg_dump -U user matchco > backup_$(date +%s).sql

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
docker build -t matchco:staging .

# Deploy to staging server
ssh ubuntu@staging.matchco.io
docker pull matchco:staging
docker-compose -f docker-compose.staging.yml up -d
```

### 2. Run Smoke Tests

```bash
# Test API endpoints
curl https://staging.matchco.io/api/courses/
curl https://staging.matchco.io/api/users/

# Test console login
→ Visit https://staging.matchco.io/console/
→ Login with test account

# Test student portal
→ Visit https://staging.matchco.io/
→ Browse courses
```

### 3. Verify Data

```bash
# Check user counts
docker exec matchco-db psql -U user matchco -c "SELECT COUNT(*) FROM accounts_user;"

# Check recent errors
docker-compose logs app | grep ERROR
```

---

## Production Deployment (Blue-Green)

### 1. Deploy to Production (Green)

```bash
# SSH into production
ssh ubuntu@matchco.io

# Deploy to green environment
docker pull matchco:latest
docker-compose -f docker-compose.green.yml up -d

# Wait 2 minutes for startup
sleep 120

# Run smoke tests
curl https://green.matchco.io/api/health/
```

### 2. Switch Traffic (Blue → Green)

```bash
# Update load balancer
aws elb modify-load-balancer-attributes \
  --load-balancer-name matchco-lb \
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
docker exec matchco-db psql -U user matchco -c "SELECT * FROM pg_stat_statements LIMIT 5;"
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
curl https://matchco.io/api/health/
```

### Database Rollback

```bash
# If database was changed
docker exec matchco-db psql -U user matchco < backup_timestamp.sql

# Verify restore
docker exec matchco-db psql -U user matchco -c "SELECT COUNT(*) FROM accounts_user;"
```

---

## Database Migrations

### Before Deploying New Code

```bash
# Test migrations on staging
docker exec matchco-staging python manage.py migrate

# Verify data integrity
docker exec matchco-staging python manage.py check

# If migration fails, rollback
docker exec matchco-db psql -U user matchco < backup.sql
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
- Status: Healthy" >> docs/development/EXECUTION_PLAN.md
```

### 2. Announce Release

```bash
# Slack notification
curl -X POST webhook.slack.com \
  -d '{"text":"🚀 MatchCo v2.1 deployed to production"}'
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
DATABASE_URL=postgresql://user:pass@rds.amazonaws.com/matchco
ALLOWED_HOSTS=matchco.io,www.matchco.io
SENTRY_DSN=https://...
```

**Staging:**
```
DEBUG=True
DATABASE_URL=postgresql://user:pass@staging-rds/matchco
ALLOWED_HOSTS=staging.matchco.io
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
docker exec matchco-db pg_dump -U user matchco > backup.sql

# Database restore
docker exec -i matchco-db psql -U user matchco < backup.sql

# Check disk space
docker exec matchco-db df -h

# View database size
docker exec matchco-db psql -U user matchco -c "\l+"
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
