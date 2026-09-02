# Notification Preferences / Communication Control Center

Patch 27 introduces a user-facing communication control center for candidate accounts.

## What changed

- Job digest preference remains synchronized with the existing `subscribers.digest_enabled` flag.
- Additional per-user preferences are persisted in `subscriber_notification_preferences`.
- The notification settings page now separates four channels:
  - new job digest
  - employer messages
  - product updates
  - security alerts
- Security alerts are shown as required in the UI because account-security events should not be silently disabled.
- Quiet hours are stored as user preference metadata for later delivery scheduling.

## API

```http
GET /api/user/me/notification-preferences
PATCH /api/user/me/notification-preferences
```

`PATCH` accepts partial updates. `quiet_hours_start` and `quiet_hours_end` must use `HH:MM` 24-hour format.

## Delivery behavior

This patch adds preference storage and user control. Existing digest delivery continues to use `digest_enabled`. Future notification workers should consult `subscriber_notification_preferences` before sending employer/product messages and before applying quiet-hour deferral.
