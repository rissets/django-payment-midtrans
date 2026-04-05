# Example Application

The `example/` directory contains a complete Django e-commerce demo that showcases all `django_midtrans` features in action.

## What's Included

- **Product catalog** with an add-to-cart flow
- **Session-based shopping cart** with quantity management
- **Checkout** with all Midtrans payment methods:
  - Credit Card (3DS with iframe modal)
  - Bank Transfer / Virtual Account (BCA, BNI, BRI, Permata, CIMB)
  - Mandiri Bill Payment (E-Channel)
  - E-Wallets (GoPay, ShopeePay, DANA)
  - QRIS (QR code)
  - Convenience Store (Indomaret, Alfamart)
  - Pay Later (Akulaku)
- **Real-time payment status** polling
- **Webhook handling** with order status sync
- **Django admin** with Unfold theme and colored badges
- **Celery** configuration for background tasks

## Project Structure

```
example/
├── manage.py
├── config/
│   ├── __init__.py          # Celery app import
│   ├── celery.py            # Celery configuration
│   ├── settings.py          # Django settings (Unfold + Midtrans)
│   ├── urls.py              # Root URL configuration
│   └── wsgi.py
├── shop/
│   ├── admin.py             # Product & Order admin (Unfold)
│   ├── apps.py
│   ├── context_processors.py # Cart context for templates
│   ├── dashboard.py          # Unfold dashboard callbacks
│   ├── models.py             # Product, Order, OrderItem
│   ├── signals.py            # Payment signal handlers
│   ├── urls.py               # Shop URL patterns
│   └── views.py              # 11 view classes
├── templates/
│   ├── base.html             # Base template with Bootstrap 5
│   ├── admin/
│   │   └── index.html        # Unfold dashboard override
│   └── shop/
│       ├── home.html          # Product listing
│       ├── cart.html          # Shopping cart
│       ├── checkout.html      # Payment method selection + processing
│       ├── order_detail.html  # Order details
│       ├── orders.html        # Order history
│       ├── payment_finish.html # Post-redirect landing
│       └── payment_status.html # Status polling page
└── db.sqlite3
```

```{toctree}
:maxdepth: 2

setup
walkthrough
```
