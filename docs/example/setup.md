# Example App Setup

## Prerequisites

- Python 3.10+
- A Midtrans sandbox account ([sign up](https://dashboard.sandbox.midtrans.com/register))

## Steps

### 1. Clone the Repository

```bash
git clone https://github.com/rissets/django-payment-midtrans.git
cd django-payment-midtrans
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```bash
pip install -e ".[dev,unfold,docs]"
```

### 4. Configure Environment

Copy the example `.env` and fill in your Midtrans sandbox credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
MIDTRANS_SERVER_KEY=SB-Mid-server-xxxxxxxxxxxxxxxxxxxx
MIDTRANS_CLIENT_KEY=SB-Mid-client-xxxxxxxxxxxxxxxxxxxx
MIDTRANS_MERCHANT_ID=G000000000
SECRET_KEY=your-django-secret-key
DEBUG=True
```

Get your sandbox credentials from the [Midtrans Dashboard](https://dashboard.sandbox.midtrans.com/) → Settings → Access Keys.

### 5. Run Migrations

```bash
cd example
python manage.py migrate
```

### 6. Create a Superuser

```bash
python manage.py createsuperuser
```

### 7. Load Sample Data (Optional)

Create some products via the admin or Django shell:

```python
python manage.py shell
```

```python
from shop.models import Product

Product.objects.create(name="T-Shirt", price=150000, stock=50, description="Cotton t-shirt")
Product.objects.create(name="Hoodie", price=350000, stock=30, description="Premium hoodie")
Product.objects.create(name="Cap", price=75000, stock=100, description="Baseball cap")
```

### 8. Start the Server

```bash
python manage.py runserver
```

Visit:
- **Shop**: http://localhost:8000/
- **Admin**: http://localhost:8000/admin/
- **API**: http://localhost:8000/midtrans/api/

### 9. (Optional) Start Celery

For background payment tasks:

```bash
# In a separate terminal
celery -A config worker -B -l info
```

### 10. (Optional) Expose for Webhooks

To receive Midtrans notifications locally:

```bash
ngrok http 8000
```

Then set the notification URL in your `.env`:

```ini
MIDTRANS_NOTIFICATION_URL=https://abc123.ngrok-free.app/midtrans/api/notification/
```

Or configure it directly in the [Midtrans Dashboard](https://dashboard.sandbox.midtrans.com/) → Settings → Payment → Notification URL.
