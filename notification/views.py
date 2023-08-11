from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from django.http import JsonResponse
from webpush import send_user_notification
from .models import PushNotificationSubscriber

import environ

env = environ.Env()
environ.Env.read_env()


@method_decorator(csrf_exempt, name="dispatch")
class PushNotificationSubscribeView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user_id = data.get("user_id")
            device_token = data.get("device_token")

            # Save the subscription to your database
            PushNotificationSubscriber.objects.create(
                user_id=user_id, device_token=device_token
            )

            return JsonResponse({"message": "Subscription saved successfully."})
        except Exception as e:
            return JsonResponse({"error": "An error occurred.", "details": str(e)})


def send_push_notification(request):
    user_subscriptions = get_user_subscriptions(request.user.id)
    payload = {
        "title": "Notification Title",
        "body": "Notification Body",
    }

    for subscription in user_subscriptions:
        send_user_notification(
            user=subscription.user,
            payload=json.dumps(payload),
            ttl=1000,  # Time-to-live for the notification
            vapid_private_key=env("VAPID_PRIVATE_KEY"),
            vapid_claims={"sub": "mailto:your_email@example.com"},
        )

    return JsonResponse({"message": "Push notifications sent successfully."})


def get_user_subscriptions(user_id):
    try:
        subscriptions = PushNotificationSubscriber.objects.filter(user_id=user_id)
        return subscriptions
    except PushNotificationSubscriber.DoesNotExist:
        return []
