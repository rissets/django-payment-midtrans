from datetime import timedelta

from django.db.models import Count, Sum
from django.utils import timezone

from django_midtrans.constants import TransactionStatus
from django_midtrans.models import MidtransPayment


def dashboard_callback(request, context):
    today = timezone.now()
    payments = MidtransPayment.objects.all()

    total_payments = payments.count()
    total_revenue = (
        payments.filter(transaction_status__in=TransactionStatus.SUCCESS_STATUSES)
        .aggregate(total=Sum("gross_amount"))["total"]
        or 0
    )
    pending_count = payments.filter(transaction_status=TransactionStatus.PENDING).count()
    today_count = payments.filter(created_at__date=today.date()).count()

    # Status distribution chart
    status_counts = (
        payments.values("transaction_status")
        .annotate(count=Count("id"))
        .order_by("transaction_status")
    )
    color_map = {
        "pending": "#f59e0b",
        "capture": "#10b981",
        "settlement": "#10b981",
        "deny": "#ef4444",
        "cancel": "#ef4444",
        "expire": "#6b7280",
        "refund": "#3b82f6",
        "partial_refund": "#8b5cf6",
        "authorize": "#f59e0b",
        "failure": "#ef4444",
    }
    status_labels = [s["transaction_status"].title() for s in status_counts]
    status_data = [s["count"] for s in status_counts]
    status_colors = [color_map.get(s["transaction_status"], "#6b7280") for s in status_counts]

    # Daily revenue chart (last 7 days)
    daily_labels = []
    daily_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        daily_labels.append(day.strftime("%d %b"))
        day_total = (
            payments.filter(
                transaction_status__in=TransactionStatus.SUCCESS_STATUSES,
                created_at__date=day.date(),
            )
            .aggregate(total=Sum("gross_amount"))["total"]
            or 0
        )
        daily_data.append(float(day_total))

    recent_payments = payments[:10]

    context.update(
        {
            "total_payments": total_payments,
            "total_revenue": total_revenue,
            "pending_count": pending_count,
            "today_count": today_count,
            "status_chart": {
                "labels": status_labels,
                "datasets": [
                    {
                        "data": status_data,
                        "backgroundColor": status_colors,
                    }
                ],
            },
            "revenue_chart": {
                "labels": daily_labels,
                "datasets": [
                    {
                        "label": "Revenue (IDR)",
                        "data": daily_data,
                        "borderColor": "rgb(99, 102, 241)",
                        "backgroundColor": "rgba(99, 102, 241, 0.1)",
                        "fill": True,
                    }
                ],
            },
            "recent_payments": recent_payments,
        }
    )
    return context


def environment_callback(request):
    return ["Sandbox", "warning"]
