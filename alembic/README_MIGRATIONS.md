# Database Migrations with Alembic

This directory contains database migration scripts managed by Alembic.

## Quick Start

### Apply migrations (upgrade to latest)
```bash
alembic upgrade head
```

### Downgrade one version
```bash
alembic downgrade -1
```

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### View migration history
```bash
alembic history
```

### View current version
```bash
alembic current
```

## How It Works

Alembic tracks schema changes and allows you to:
- **Upgrade**: Apply new migrations to update the database schema
- **Downgrade**: Roll back migrations to previous states
- **Autogenerate**: Automatically detect model changes and create migrations

## Configuration

- **alembic.ini**: Database connection and Alembic settings
- **alembic/env.py**: Python environment configuration
- **alembic/versions/**: Migration scripts (auto-generated)

## Best Practices

1. **Always review auto-generated migrations** before applying them
2. **Test migrations** in a development environment first
3. **Commit migrations to git** along with model changes
4. **Never edit applied migrations** - create a new one instead
5. **Use descriptive migration messages**

## Common Commands

```bash
# Create empty migration (manual)
alembic revision -m "add user table"

# Auto-generate from model changes
alembic revision --autogenerate -m "add email field to user"

# Apply all pending migrations
alembic upgrade head

# Rollback to specific version
alembic downgrade <revision>

# Show SQL without applying
alembic upgrade head --sql

# Downgrade to base (WARNING: drops all tables)
alembic downgrade base
```

## Troubleshooting

**Issue**: Migration conflicts
- Resolution: Review migration order and dependencies

**Issue**: Auto-generate not detecting changes
- Resolution: Ensure models are imported in env.py

**Issue**: Database locked (SQLite)
- Resolution: Close all connections to the database

## Database URL

The database URL is configured in `alembic.ini`:
```ini
sqlalchemy.url = sqlite:///data/applications.db
```

For production, update this to your database URL (PostgreSQL, MySQL, etc.)
