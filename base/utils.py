from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

channel_layer = get_channel_layer()


def log_admin(message):
    async_to_sync(channel_layer.group_send)(
        "admin_group",
        {
            "type": "log_entry",
            "message": message,
            "timestamp": timezone.now().isoformat(),
        },
    )
