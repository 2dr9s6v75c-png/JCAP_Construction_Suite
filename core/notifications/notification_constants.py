class NotificationEntity:
    """
    Standard entity identifiers used by persistent notifications.

    These values are stored in core.notifications.entity_type.
    """

    CLARIFICATION = "clarification"
    MATERIAL_REQUEST = "material_request"
    PURCHASE_ORDER = "purchase_order"
    INVOICE = "invoice"
    INVENTORY = "inventory"


class NotificationType:
    """
    Standard notification type identifiers.

    These values are stored in
    core.notifications.notification_type.
    """

    CLARIFICATION_REQUESTED = (
        "CLARIFICATION_REQUESTED"
    )

    CLARIFICATION_RESPONSE_RECEIVED = (
        "CLARIFICATION_RESPONSE_RECEIVED"
    )

    CLARIFICATION_FORWARDED = (
        "CLARIFICATION_FORWARDED"
    )

    CLARIFICATION_RESOLVED = (
        "CLARIFICATION_RESOLVED"
    )

    CLARIFICATION_REOPENED = (
        "CLARIFICATION_REOPENED"
    )

    ADDITIONAL_DOCUMENT_UPLOADED = (
        "ADDITIONAL_DOCUMENT_UPLOADED"
    )