from hiring_radar.api.schemas.auth import AdminAuthMeResponse, AdminLoginRequest
from hiring_radar.api.schemas.dashboard import (
    DashboardDigestFilterPolicyResponse,
    DashboardJobCountsResponse,
    DashboardLatestRunResponse,
    DashboardSubscriberCountsResponse,
    DashboardSummaryResponse,
)
from hiring_radar.api.schemas.jobs import (
    AdminJobListItemResponse,
    AdminJobListResponse,
)
from hiring_radar.api.schemas.runs import (
    AdminCrawlRunListItemResponse,
    AdminCrawlRunListResponse,
    AdminNotificationRunListItemResponse,
    AdminNotificationRunListResponse,
)
from hiring_radar.api.schemas.settings import (
    AdminFilterPreviewFieldMatchResponse,
    AdminFilterPreviewSampleResponse,
    AdminSettingsFilterPreviewRequest,
    AdminSettingsFilterPreviewResponse,
    AdminSettingsKeywordFilterResponse,
    AdminSettingsKeywordFilterUpdate,
    AdminSettingsNotificationsResponse,
    AdminSettingsNotificationsUpdate,
    AdminSettingsResponse,
    AdminSettingsUpdateRequest,
)
from hiring_radar.api.schemas.subscribers import (
    AdminSubscriberListItemResponse,
    AdminSubscriberListResponse,
    AdminSubscriberUpdateRequest,
)
from hiring_radar.api.schemas.user_auth import (
    UserAuthMeResponse,
    UserConsumeMagicLinkRequest,
    UserRequestMagicLinkRequest,
    UserRequestMagicLinkResponse,
)
from hiring_radar.api.schemas.user_me import (
    UserFilterPolicyResponse,
    UserMeResponse,
    UserPreferencesUpdateRequest,
)

__all__ = [
    "AdminAuthMeResponse",
    "AdminCrawlRunListItemResponse",
    "AdminCrawlRunListResponse",
    "AdminFilterPreviewFieldMatchResponse",
    "AdminFilterPreviewSampleResponse",
    "AdminJobListItemResponse",
    "AdminJobListResponse",
    "AdminLoginRequest",
    "AdminNotificationRunListItemResponse",
    "AdminNotificationRunListResponse",
    "AdminSettingsFilterPreviewRequest",
    "AdminSettingsFilterPreviewResponse",
    "AdminSettingsKeywordFilterResponse",
    "AdminSettingsKeywordFilterUpdate",
    "AdminSettingsNotificationsResponse",
    "AdminSettingsNotificationsUpdate",
    "AdminSettingsResponse",
    "AdminSettingsUpdateRequest",
    "AdminSubscriberListItemResponse",
    "AdminSubscriberListResponse",
    "AdminSubscriberUpdateRequest",
    "DashboardDigestFilterPolicyResponse",
    "DashboardJobCountsResponse",
    "DashboardLatestRunResponse",
    "DashboardSubscriberCountsResponse",
    "DashboardSummaryResponse",
    "UserAuthMeResponse",
    "UserConsumeMagicLinkRequest",
    "UserFilterPolicyResponse",
    "UserMeResponse",
    "UserPreferencesUpdateRequest",
    "UserRequestMagicLinkRequest",
    "UserRequestMagicLinkResponse",
]