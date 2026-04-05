# Example App Walkthrough

This guide walks through the complete payment flow in the example shop application.

## 1. Browse Products

Visit http://localhost:8000/ to see the product catalog.

Each product card shows name, price, description, and an **Add to Cart** button.

## 2. Add to Cart

Click **Add to Cart** on any product. The session-based cart tracks items and quantities.

The cart icon in the navigation bar shows the current item count.

## 3. View Cart

Click the cart icon or visit http://localhost:8000/cart/ to view your cart.

From here you can:
- Update quantities
- Remove items
- See the total amount
- Proceed to checkout

## 4. Checkout

Click **Checkout** (requires login). The checkout page shows:
- Order summary with items and total
- Payment method selector

### Available Payment Methods

| Method | What Happens |
|--------|-------------|
| **Credit Card** | Card input form → tokenization → 3DS iframe modal |
| **BCA/BNI/BRI/Permata/CIMB VA** | Displays Virtual Account number to transfer to |
| **Mandiri Bill** | Displays biller code + bill key |
| **GoPay** | Shows QR code + deeplink button (opens GoPay app) |
| **ShopeePay** | Redirects to ShopeePay for payment |
| **DANA** | Redirects to DANA for payment |
| **QRIS** | Displays QR code image |
| **Indomaret/Alfamart** | Displays payment code for counter |
| **Akulaku** | Redirects to Akulaku installment page |

## 5. Complete Payment

### Credit Card Flow

1. Enter test card number: `4811 1111 1111 1114`
2. Expiry: any future date (e.g., `12/28`)
3. CVV: `123`
4. Click **Pay**
5. 3DS authentication opens in an iframe modal
6. Complete the 3DS challenge (OTP: `112233` for challenge cards)
7. Payment settles immediately

### Bank Transfer Flow

1. Select a bank (e.g., BCA)
2. Click **Pay**
3. Copy the Virtual Account number displayed
4. In sandbox: use the [Midtrans Simulator](https://simulator.sandbox.midtrans.com/) to simulate payment
5. Status updates via webhook or polling

### E-Wallet Flow

1. Select GoPay, ShopeePay, or DANA
2. Click **Pay**
3. For GoPay: scan QR or click deeplink
4. For ShopeePay/DANA: complete on the redirected page
5. Return to the app — status is updated

### QRIS Flow

1. Select QRIS
2. Click **Pay**
3. Scan the displayed QR code with any QRIS-compatible e-wallet
4. In sandbox: use the [QRIS Simulator](https://simulator.sandbox.midtrans.com/qris/index)

### Convenience Store Flow

1. Select Indomaret or Alfamart
2. Click **Pay**
3. Note the payment code displayed
4. In sandbox: use the simulator to confirm payment

## 6. Payment Status

After payment, you're redirected to the **Payment Status** page.

This page:
- Shows the current payment status with a colored badge
- Auto-polls the server every 3 seconds for status updates
- Displays payment details (VA number, payment code, etc.)
- Shows a success/failure message when the status becomes final

## 7. Order History

Visit http://localhost:8000/orders/ to see all your orders.

Each order shows:
- Order ID
- Date
- Status (colored badge)
- Total amount

Click an order to see full details including payment information and line items.

## 8. Admin Dashboard

Visit http://localhost:8000/admin/ and log in as superuser.

### Payment Management

Navigate to **Midtrans Payments** to see all payments with:
- Colored status badges
- Filters by payment type, status, date range
- Search by order ID or customer email
- Click a payment to see full details
- Actions: Check Status, Cancel, Expire (Unfold theme only)

### Order Management

Navigate to **Orders** to manage shop orders linked to their Midtrans payments.

## 9. Webhook Flow

When Midtrans sends a notification:

1. POST arrives at `/midtrans/api/notification/`
2. Signature is verified
3. `MidtransPayment` status is updated
4. Signal is fired (e.g., `payment_settled`)
5. Signal handler in `shop/signals.py` updates the `Order` status

```python
# example/shop/signals.py
@receiver(payment_settled)
def handle_payment_settled(sender, payment, **kwargs):
    try:
        order = Order.objects.get(midtrans_payment=payment)
        order.status = Order.Status.PAID
        order.save()
    except Order.DoesNotExist:
        pass
```

## Sandbox Testing Tips

- Use the [Midtrans Payment Simulator](https://simulator.sandbox.midtrans.com/) to trigger payment completions
- Virtual Account payments need to be simulated — they don't auto-complete
- GoPay deeplinks expire after ~15 minutes — create a new transaction if expired
- QRIS simulator requires the raw QR string, not the image
- Credit card 3DS OTP for challenge cards: `112233`
