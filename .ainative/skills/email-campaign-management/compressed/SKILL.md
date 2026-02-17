# Email Campaign Management - Workflow

**Purpose**: Reusable workflow for email marketing campaigns with conversion tracking, trial activation.

## Campaign Database Schema

### `campaigns` Table
```sql
CREATE TABLE campaigns (
    id UUID PRIMARY KEY,
    campaign_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    trial_days INTEGER,
    tier VARCHAR(50),
    offer_expires_at TIMESTAMP
);
```

### `campaign_clicks` Table
```sql
CREATE TABLE campaign_clicks (
    id UUID PRIMARY KEY,
    campaign_id VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    click_source VARCHAR(100),
    converted BOOLEAN DEFAULT FALSE,
    converted_at TIMESTAMP,
    user_id UUID
);
```

## Campaign Statistics Query
```sql
SELECT
    COUNT(*) as total_clicks,
    COUNT(DISTINCT email) as unique_users,
    COUNT(CASE WHEN converted = TRUE THEN 1 END) as converted_count,
    ROUND(100.0 * COUNT(CASE WHEN converted = TRUE THEN 1 END) / COUNT(*), 2) as conversion_rate
FROM campaign_clicks
WHERE campaign_id = 'campaign-id-here';
```

## Resend API Integration

### Rate Limiting (CRITICAL)
```python
import time

RATE_LIMIT_DELAY = 0.5  # 2 emails per second

for email in emails:
    send_email(email)
    time.sleep(RATE_LIMIT_DELAY)
```

### Email Sending Function
```python
def send_campaign_email(email: str, campaign_id: str, template_html: str):
    payload = {
        "from": FROM_EMAIL,
        "to": [email],
        "subject": "Campaign Subject",
        "html": template_html,
        "tags": [
            {"name": "campaign", "value": campaign_id}
        ]
    }

    response = requests.post(
        RESEND_API_URL,
        headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
        json=payload
    )

    return response.status_code in [200, 201]
```

## Trial Activation Workflow
```python
def activate_trial(user, campaign_id: str, trial_days: int, plan_name: str):
    trial_end = datetime.utcnow() + timedelta(days=trial_days)

    cur.execute("""
        UPDATE subscriptions
        SET tier = 'ENTERPRISE',
            status = 'active',
            trial_ends_at = %s,
            plan_name = %s
        WHERE id = %s
    """, (trial_end, plan_name, user['subscription_id']))

    cur.execute("""
        UPDATE campaign_clicks
        SET converted = TRUE,
            converted_at = NOW(),
            user_id = %s
        WHERE id = %s
    """, (str(user['user_id']), user['click_id']))

    conn.commit()
```

## Common Pitfalls
- Use UPPERCASE enums
- Always use `status = 'active'`
- Limit to 2 emails/second
- Check `organization_id` exists
- Use template variables
- Close DB connections

## Email Template Requirements
```html
<a href="https://www.ainative.studio/register?gift={{campaign_id}}&email={{email}}">
    Claim Your Trial
</a>
```

## Quick Reference Commands
```bash
# Check Campaign Stats
railway run psql -c "
SELECT COUNT(*), COUNT(DISTINCT email), COUNT(CASE WHEN converted THEN 1 END)
FROM campaign_clicks
WHERE campaign_id = 'campaign-id';
"

# Send Reminder Campaign
railway run python3 scripts/send_reminder.py --yes
```

## Campaign Checklist
- [ ] Create campaign record
- [ ] Add to backend config
- [ ] Create email templates
- [ ] Test email send
- [ ] Deploy changes
- [ ] Launch campaign
- [ ] Monitor conversions
- [ ] Send reminders
- [ ] Activate trials
- [ ] Generate report