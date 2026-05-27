# Subscription Module Documentation

## Overview

The subscription module is a comprehensive system that allows doctors to subscribe to different service plans with a dummy payment system. This module is managed through the admin section and provides a complete subscription lifecycle management experience.

## Features

### 1. **Subscription Plans**
- **Three Default Plans:**
  - **Basic**: $29.99/month - 50 appointments/month
  - **Professional**: $79.99/month - 200 appointments/month
  - **Premium**: $149.99/month - 500 appointments/month

- **Admin Capabilities:**
  - Create new subscription plans
  - Edit existing plans
  - Delete plans
  - Toggle plan active/inactive status
  - Manage plan features and pricing

### 2. **Doctor Subscription Management**
- Doctors can view available subscription plans
- Subscribe to any active plan
- View current active subscription details
- Track appointment usage against plan limits
- Cancel subscriptions
- View subscription history

### 3. **Payment System (Dummy)**
- **Payment Methods:**
  - QR Code / UPI (Primary & Exclusive method)

- **Features:**
  - Instant dynamic QR generation for each plan
  - One-click verification after payment
  - Mobile-optimized payment experience
  - Secure payment form with input formatting
  - Transaction ID generation
  - Payment status tracking
  - Order summary display
  - Demo mode with dummy transaction processing

### 4. **Admin Dashboard**
- Comprehensive subscription management interface
- Three-tab interface:
  - **Subscription Plans**: View, create, edit, delete plans
  - **Active Subscriptions**: Monitor all doctor subscriptions
  - **Payment History**: Track all payments and transactions

## Database Models

### SubscriptionPlan
```python
- id: Integer (Primary Key)
- name: String (Unique)
- description: Text
- price: Float
- duration_days: Integer
- max_appointments: Integer
- features: Text (JSON string)
- is_active: Boolean
- date_created: DateTime
```

### DoctorSubscription
```python
- id: Integer (Primary Key)
- doctor_id: Integer (Foreign Key)
- plan_id: Integer (Foreign Key)
- start_date: DateTime
- end_date: DateTime
- status: String (active, expired, cancelled)
- appointments_used: Integer
- date_created: DateTime
```

### Payment
```python
- id: Integer (Primary Key)
- doctor_id: Integer (Foreign Key)
- subscription_id: Integer (Foreign Key)
- amount: Float
- payment_method: String (credit_card, paypal, bank_transfer)
- transaction_id: String (Unique)
- status: String (completed, pending, failed)
- date_created: DateTime
```

## API Routes

### Doctor Routes

#### View Subscriptions
- **Route**: `/doctor/subscriptions`
- **Method**: GET
- **Auth**: Required (Doctor)
- **Description**: Display doctor's subscriptions and available plans

#### Subscribe to Plan
- **Route**: `/doctor/subscribe/<plan_id>`
- **Method**: POST
- **Auth**: Required (Doctor)
- **Description**: Initiate subscription to a plan

#### Process Payment
- **Route**: `/doctor/payment/<plan_id>`
- **Method**: GET, POST
- **Auth**: Required (Doctor)
- **Description**: Display payment form and process payment

#### Cancel Subscription
- **Route**: `/doctor/cancel_subscription/<subscription_id>`
- **Method**: POST
- **Auth**: Required (Doctor)
- **Description**: Cancel an active subscription

### Admin Routes

#### View Subscriptions Dashboard
- **Route**: `/admin/subscriptions`
- **Method**: GET
- **Auth**: Required (Admin)
- **Description**: View all plans, subscriptions, and payments

#### Create Subscription Plan
- **Route**: `/admin/create_plan`
- **Method**: GET, POST
- **Auth**: Required (Admin)
- **Description**: Create a new subscription plan

#### Edit Subscription Plan
- **Route**: `/admin/edit_plan/<plan_id>`
- **Method**: GET, POST
- **Auth**: Required (Admin)
- **Description**: Edit an existing subscription plan

#### Delete Subscription Plan
- **Route**: `/admin/delete_plan/<plan_id>`
- **Method**: POST
- **Auth**: Required (Admin)
- **Description**: Delete a subscription plan

## Templates

### Doctor Templates

#### `doctor_subscriptions.html`
- Display current active subscription
- Show subscription details and usage
- Display available plans for purchase
- Show subscription history
- Features: Plan comparison, usage progress bar, feature list

#### `payment_page.html`
- Payment method selection
- Credit card form with validation
- Order summary
- Terms and conditions
- Demo mode notice

### Admin Templates

#### `admin_subscriptions.html`
- Tabbed interface for plans, subscriptions, and payments
- Plan management cards
- Subscription monitoring table
- Payment history table
- Quick actions for plan management

#### `create_subscription_plan.html`
- Form to create new subscription plans
- Input fields for all plan attributes
- Tips and guidelines for plan creation

#### `edit_subscription_plan.html`
- Form to edit existing plans
- Plan information display
- Active/inactive toggle

## Usage Workflow

### For Doctors

1. **Login** to doctor account
2. **Navigate** to "My Subscription" from dashboard
3. **View** current subscription status (if any)
4. **Browse** available plans
5. **Click** "Subscribe Now" on desired plan
6. **Complete** payment form
7. **Confirm** subscription
8. **Track** appointment usage against plan limits

### For Admins

1. **Login** to admin account
2. **Navigate** to "Manage Subscriptions" from admin dashboard
3. **Create Plans**: Set up subscription tiers
4. **Monitor Subscriptions**: Track active doctor subscriptions
5. **Review Payments**: Check payment history and transactions
6. **Edit Plans**: Update pricing and features
7. **Manage Status**: Activate/deactivate plans as needed

## Sample Data

The application includes three pre-configured subscription plans (in Indian Rupees):

```
Basic Plan
- Price: ₹2,499/month
- Duration: 30 days
- Max Appointments: 50/month
- Features: Basic analytics, Email support

Professional Plan
- Price: ₹6,999/month
- Duration: 30 days
- Max Appointments: 200/month
- Features: Advanced analytics, Priority support, Patient messaging

Premium Plan
- Price: ₹12,999/month
- Duration: 30 days
- Max Appointments: 500/month
- Features: Full analytics, 24/7 support, API access, Custom branding
```

## Dummy Payment System

The payment system is designed for demonstration purposes:

- **No Real Charges**: All payments are simulated
- **Transaction IDs**: Generated using UUID format (TXN-XXXXXXXXXXXXXXXX)
- **Payment Methods**: Support for Credit Card, PayPal, and Bank Transfer
- **Status**: All payments are marked as "completed"
- **Demo Mode**: Clear indication that this is a dummy system

### Testing Payment

1. Select any payment method
2. For credit card: Use any card number (validation is basic)
3. Enter any expiry date and CVV
4. Submit the form
5. Transaction will be processed immediately
6. Subscription will be activated

## Integration Points

### With Existing System

- **Doctor Model**: Extended with subscriptions relationship
- **Appointment Tracking**: Can track appointments used per subscription
- **Admin Dashboard**: Added subscription management link
- **Doctor Dashboard**: Added subscription management link

### Future Enhancements

- Real payment gateway integration (Stripe, PayPal)
- Automatic subscription renewal
- Usage analytics and reporting
- Subscription tier upgrades/downgrades
- Promotional codes and discounts
- Invoice generation and email
- Subscription expiration notifications
- Appointment limit enforcement

## Security Considerations

- All routes require authentication
- Doctor-specific routes verify doctor ownership
- Admin-only routes verify admin privileges
- Payment data is not stored (dummy system)
- Transaction IDs are unique and trackable
- CSRF protection via Flask-WTF (if enabled)

## Configuration

### Default Admin Credentials
- Email: `admin@healthcare.com`
- Password: `admin123`

### Database
- SQLite database with automatic table creation
- Sample data populated on first run
- Cascading deletes for related records

## Troubleshooting

### Issue: Subscription not appearing
- **Solution**: Ensure doctor is logged in and plan is active

### Issue: Payment form not showing
- **Solution**: Check that payment method is selected

### Issue: Subscription limit reached
- **Solution**: Doctor must cancel current subscription before subscribing to another

### Issue: Database errors
- **Solution**: Run `flask db upgrade` or delete `healthcare.db` to reset

## API Response Examples

### Get Subscriptions (Doctor)
```json
{
  "active_subscription": {
    "id": 1,
    "plan_name": "Professional",
    "price": 79.99,
    "appointments_used": 45,
    "max_appointments": 200,
    "end_date": "2024-01-15"
  },
  "available_plans": [...]
}
```

### Create Payment
```json
{
  "success": true,
  "transaction_id": "TXN-ABC123DEF456",
  "subscription_id": 1,
  "amount": 79.99,
  "status": "completed"
}
```

## Support

For issues or questions about the subscription module:
1. Check this documentation
2. Review the code comments in `app.py`
3. Check the template files for UI details
4. Verify database schema in models

## License

This subscription module is part of the Healthcare Management System.
