# Production Deployment

This guide covers deploying `django_midtrans` in a production environment.

## Environment Variables

Set these in your server environment (not in code):

```bash
# Midtrans Credentials (Production)
MIDTRANS_SERVER_KEY=Mid-server-xxxxxxxxxxxxxxxxxxxx
MIDTRANS_CLIENT_KEY=Mid-client-xxxxxxxxxxxxxxxxxxxx
MIDTRANS_MERCHANT_ID=Mxxxxxxxxx
MIDTRANS_IS_PRODUCTION=True
MIDTRANS_NOTIFICATION_URL=https://yourdomain.com/midtrans/api/notification/
```

```python
# settings.py — Read from environment
import os

MIDTRANS = {
    "SERVER_KEY": os.environ["MIDTRANS_SERVER_KEY"],
    "CLIENT_KEY": os.environ["MIDTRANS_CLIENT_KEY"],
    "MERCHANT_ID": os.environ["MIDTRANS_MERCHANT_ID"],
    "IS_PRODUCTION": os.environ.get("MIDTRANS_IS_PRODUCTION", "").lower() == "true",
    "NOTIFICATION_URL": os.environ["MIDTRANS_NOTIFICATION_URL"],
}
```

## Production Checklist

| Item | Description |
|------|-------------|
| Use **production** keys | Replace `SB-Mid-server-*` with `Mid-server-*` |
| Set `IS_PRODUCTION: True` | Switches API base URL to `api.midtrans.com` |
| Set `NOTIFICATION_URL` | Must be HTTPS and publicly accessible |
| Configure `ALLOWED_HOSTS` | Include your domain |
| Enable `HTTPS` | Required for webhooks and 3DS redirects |
| Set `DEBUG = False` | Never run debug mode in production |
| Use a process manager | Gunicorn, uWSGI, or Daphne |
| Run Celery workers | For background tasks and periodic jobs |
| Run Celery Beat | For periodic payment checks |
| Set up database backups | Payment data is critical |
| Configure logging | Log payment events for audit trails |

## HTTPS Configuration

Midtrans requires HTTPS for:
- Webhook notification URLs
- 3DS redirect callbacks
- ShopeePay/DANA redirect URLs

```python
# settings.py
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .[dev]

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### docker-compose.yml

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
      - redis

  celery:
    build: .
    command: celery -A config worker -l info
    env_file: .env
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    command: celery -A config beat -l info
    env_file: .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: midtrans_db
      POSTGRES_USER: midtrans
      POSTGRES_PASSWORD: ${DB_PASSWORD}

  redis:
    image: redis:7-alpine

volumes:
  pgdata:
```

## Nginx Configuration

```nginx
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    location /static/ {
        alias /app/staticfiles/;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Logging

Configure payment-specific logging:

```python
# settings.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "payment_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "/var/log/app/payments.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django_midtrans": {
            "handlers": ["payment_file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}
```

## Database Considerations

- Use PostgreSQL for production (SQLite is not suitable)
- Index `order_id` and `transaction_status` fields (already indexed by default)
- Set up regular database backups
- Consider read replicas for high-traffic dashboards

```python
# settings.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}
```

## Monitoring

Key metrics to monitor:

| Metric | Why |
|--------|-----|
| Pending payment count | Detect stuck payments |
| Webhook response time | Ensure fast processing |
| Failed notification count | Detect integration issues |
| Payment success rate | Business health indicator |
| Celery queue length | Detect backlog |

Use Django signals to emit metrics to your monitoring system:

```python
import time
from django_midtrans.signals import payment_settled, payment_failed

@receiver(payment_settled)
def track_settlement(sender, payment, **kwargs):
    statsd.incr("payments.settled")
    statsd.gauge("payments.amount", float(payment.gross_amount))

@receiver(payment_failed)
def track_failure(sender, payment, **kwargs):
    statsd.incr("payments.failed")
```
