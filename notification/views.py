from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from user.models import User
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
            endpoint = data.get("endpoint")
            user_id = data.get("user_id")

            # Save the subscription to your database
            PushNotificationSubscriber.objects.create(
                user_id=user_id, device_token=endpoint
            )

            send_push_notification(user_id)

            return JsonResponse({"message": "Subscription saved successfully."})
        except Exception as e:
            return JsonResponse({"error": "An error occurred.", "details": str(e)})


def send_push_notification(user_id):
    user_subscriptions = get_user_subscriptions(user_id)
    user = User.objects.get(id=user_id)
    payload = {
        "title": "Notification Title",
        "body": "Notification Body",
    }

    push_infos = user.webpush_info.select_related("subscription")
    for push_info in push_infos:
        print(push_info)

    for subscription in user_subscriptions:
        send_user_notification(
            user=subscription.user,
            payload=payload,
            ttl=1000,  # Time-to-live for the notification
        )

    return JsonResponse({"message": "Push notifications sent successfully."})


def get_user_subscriptions(user_id):
    try:
        subscriptions = PushNotificationSubscriber.objects.filter(user_id=user_id)
        return subscriptions
    except PushNotificationSubscriber.DoesNotExist:
        return []
