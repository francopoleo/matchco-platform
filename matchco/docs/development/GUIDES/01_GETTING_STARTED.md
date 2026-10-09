# Getting Started - MatchCo Platform

**For:** Developers setting up local environment  
**Time:** 10 minutes

---

## Prerequisites

- Docker & Docker Compose
- Python 3.12+
- PostgreSQL 13+ (via Docker)
- Git

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/francopoleo/matchco-platform.git
cd matchco-platform
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` with your settings:
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@db:5432/matchco
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 3. Start Docker Containers

```bash
docker-compose up -d
```

This starts:
- Django app (port 8000)
- PostgreSQL database (port 5432)

### 4. Run Migrations & Setup

```bash
docker exec matchco-app ./setup.sh
```

Or manually:
```bash
docker exec matchco-app python manage.py makemigrations
docker exec matchco-app python manage.py migrate
docker exec matchco-app python manage.py collectstatic --noinput
docker exec matchco-app python manage.py seed_complete_system
```

Os dados de demonstração são criados pelos comandos `seed_*` atuais. O projeto
não usa mais um comando genérico `import_fixtures`.

### 5. Create Superuser

```bash
docker exec -it matchco-app python manage.py createsuperuser
```

### 6. Access Application

- **Console (Admin):** http://localhost:8000/console/
- **Student Portal:** http://localhost:8000/
- **Django Admin:** http://localhost:8000/admin/

---

## Verify Setup

```bash
# Check containers running
docker-compose ps

# View logs
docker-compose logs -f app

# Test database connection
docker exec matchco-app python manage.py shell
>>> from django.db import connection
>>> connection.cursor()
```

---

## Common Commands

```bash
# Stop containers
docker-compose down

# View logs
docker-compose logs app

# Run tests
docker exec matchco-app python manage.py test

# Create database backup
docker exec matchco-db pg_dump -U user matchco > backup.sql

# Shell access
docker exec -it matchco-app /bin/bash
```

---

## Troubleshooting

**Port already in use:**
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

**Database connection error:**
```bash
# Restart database
docker-compose restart db
```

**Permission denied:**
```bash
# Fix permissions
sudo chown -R $USER:$USER .
```

---

## Next Steps

- Read: `02_WORKFLOW.md` - Development workflow
- See: `REFERENCES/ARCHITECTURE.md` - System design
- Check: GitHub Issues for tasks

---

**Questions?** See `.github/GITHUB_WORKFLOW.md`
