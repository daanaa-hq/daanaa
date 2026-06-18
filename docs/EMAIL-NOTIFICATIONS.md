# Email Notifications Setup

This document describes the email notification system for Daanaa, including configuration, templates, and deployment.

## Overview

Email notifications are sent to volunteers when:
- ✓ A nonprofit verifies their volunteer hours
- ✓ A nonprofit rejects their volunteer hours

Notifications are optional and can be disabled via configuration.

## Email Service

The email service (`scripts/email_service.py`) provides:

- **EmailService**: Sends emails via SMTP
- **EmailTemplate**: HTML + plain text email format
- **Templates**: `hours_verified_email()`, `hours_rejected_email()`

### Configuration

Email notifications are controlled by environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `EMAIL_ENABLED` | `false` | Enable/disable email sending (set to `true` to enable) |
| `SMTP_HOST` | `localhost` | SMTP server hostname |
| `SMTP_PORT` | `1025` | SMTP server port |
| `SMTP_USER` | (empty) | SMTP username (optional) |
| `SMTP_PASSWORD` | (empty) | SMTP password (optional) |
| `FROM_EMAIL` | `noreply@daanaa.org` | Sender email address |

### Email Service Providers

For production, use one of these services:

#### Option 1: SendGrid

```bash
# Install SendGrid Python library
pip install sendgrid

# Set environment variables
export SMTP_HOST="smtp.sendgrid.net"
export SMTP_PORT="587"
export SMTP_USER="apikey"  # Literal string "apikey"
export SMTP_PASSWORD="SG.xxxxx"  # Your SendGrid API key
export FROM_EMAIL="noreply@daanaa.org"
export EMAIL_ENABLED="true"
```

#### Option 2: Mailgun

```bash
# Set environment variables
export SMTP_HOST="smtp.mailgun.org"
export SMTP_PORT="587"
export SMTP_USER="postmaster@daanaa.org"
export SMTP_PASSWORD="your-mailgun-password"
export FROM_EMAIL="noreply@daanaa.org"
export EMAIL_ENABLED="true"
```

#### Option 3: AWS SES

```bash
# Set environment variables
export SMTP_HOST="email-smtp.us-east-1.amazonaws.com"  # Change region as needed
export SMTP_PORT="587"
export SMTP_USER="your-ses-smtp-user"
export SMTP_PASSWORD="your-ses-smtp-password"
export FROM_EMAIL="noreply@daanaa.org"
export EMAIL_ENABLED="true"
```

#### Option 4: Local Testing (MailHog)

For local development, use MailHog to test emails without sending:

```bash
# Install MailHog (https://github.com/mailhog/MailHog)
# macOS: brew install mailhog
# Linux: wget https://github.com/mailhog/MailHog/releases/download/v1.0.1/MailHog_linux_amd64

# Run MailHog
mailhog

# MailHog listens on:
# - SMTP: localhost:1025 (default in Daanaa)
# - Web UI: http://localhost:8025

# Set environment variable
export EMAIL_ENABLED="true"

# No username/password needed for MailHog
```

## Email Templates

### Verified Hours Email

**Subject**: `✓ Your volunteer hours with [nonprofit] have been verified`

**Content**:
- Congratulations message
- Nonprofit name, date, hours, notes
- Link to Daanaa Impact Wallet
- Privacy reassurance

**Example**:
```
From: noreply@daanaa.org
To: volunteer@example.com
Subject: ✓ Your volunteer hours with Red Cross have been verified

Hello,

Good news! Red Cross has verified your volunteer hours.

Details:
- Date: 2026-06-18
- Hours: 5.0
- Notes: Event setup and registration desk

You can view this and other volunteer hours in your Daanaa Impact Wallet:
https://daanaa.org/wallet

Your volunteer record helps us understand community impact. Thank you for your service!

Best regards,
The Daanaa Team
https://daanaa.org
```

### Rejected Hours Email

**Subject**: `Your volunteer hours with [nonprofit] could not be verified`

**Content**:
- Explanation that hours couldn't be verified
- Nonprofit name, date, hours, rejection reason
- Link to Daanaa Impact Wallet
- Instructions to contact nonprofit if disputed

**Example**:
```
From: noreply@daanaa.org
To: volunteer@example.com
Subject: Your volunteer hours with Red Cross could not be verified

Hello,

We wanted to let you know that Red Cross could not verify your volunteer hours.

Details:
- Date: 2026-06-18
- Hours: 5.0
- Reason: We don't have a record of this event

You can view this and contact the nonprofit through your Daanaa Impact Wallet:
https://daanaa.org/wallet

If you believe this was an error, please reach out to the nonprofit directly or contact us.

Best regards,
The Daanaa Team
https://daanaa.org
```

## Backend Integration

When a nonprofit verifies or rejects hours, the backend:

1. Updates the volunteer_hour_logs status in SQLite
2. Prepares the email template
3. Queues the email for sending (if EMAIL_ENABLED=true)
4. Logs the action to audit_logs

**Endpoint**: `POST /api/nonprofit/verify-hours`

```json
{
  "record_id": "volunteer_log_id",
  "action": "verify",  // or "reject"
  "message": "Verified",  // for verify action
  "reason": "Dates don't match"  // for reject action
}
```

## Testing

### Local Testing with MailHog

1. Start MailHog:
   ```bash
   mailhog
   ```

2. Set environment variables:
   ```bash
   export EMAIL_ENABLED="true"
   export SMTP_HOST="localhost"
   export SMTP_PORT="1025"
   ```

3. Restart the API:
   ```bash
   python daanaa_api.py
   ```

4. Verify hours through the nonprofit dashboard

5. Check the MailHog UI at `http://localhost:8025` to see the email

### Production Testing

1. Set real email service credentials
2. Verify a test entry with a known email address
3. Check that email is received
4. Verify email content and formatting

## Audit Logging

All hour verification actions are logged to `volunteer_hour_logs` in SQLite:
- `verified_at`: Timestamp when verified
- `verified_by`: UID of nonprofit staff who verified
- `verification_message`: Message from staff
- `rejection_reason`: Reason for rejection (if rejected)

For future enhancement, add to `audit_logs` collection in Firestore:
- Action: "hours_verified" or "hours_rejected"
- Timestamp
- Nonprofit EIN
- Volunteer UID
- Message/reason

## Future Enhancements

- [ ] Use SendGrid for production email sending
- [ ] Add email verification on signup to prevent invalid addresses
- [ ] Create unsubscribe link for notifications
- [ ] Add batch sending with retry logic
- [ ] Track email open rates and bounces
- [ ] Add digest email summarizing all verified hours weekly
- [ ] Create email preferences in user wallet (opt-in/out)
- [ ] Add SMS option for critical notifications

## Troubleshooting

### Emails Not Sending

1. **Check EMAIL_ENABLED**:
   ```bash
   echo $EMAIL_ENABLED
   # Should be "true"
   ```

2. **Check SMTP credentials**:
   ```bash
   python3 -c "
   import smtplib
   server = smtplib.SMTP('smtp.sendgrid.net', 587)
   server.starttls()
   server.login('apikey', 'SG.xxxxx')
   server.quit()
   print('SMTP connection successful')
   "
   ```

3. **Check API logs**:
   ```bash
   grep -i email /var/log/daanaa_api.log
   ```

4. **Test with MailHog**:
   ```bash
   export EMAIL_ENABLED="true"
   export SMTP_HOST="localhost"
   export SMTP_PORT="1025"
   # Restart API and verify hours
   # Check http://localhost:8025
   ```

### Email Address Issues

Currently, the email service requires the volunteer's email address. This needs to be:
1. Stored in Firestore user profile
2. Fetched from Firestore when sending the email

This is implemented in `scripts/email_service.py` but requires the email to be passed from the backend when calling the template.

## Related Documentation

- [FIRESTORE-SETUP.md](./FIRESTORE-SETUP.md) - Firestore collections and structure
- [WALLET-SETUP.md](./WALLET-SETUP.md) - Wallet API and authentication
- [daanaa_api.py](../daanaa_api.py) - Backend API (email integration around line 5770)
