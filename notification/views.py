# import json
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator
# from django.views import View

# # from webpush import send_user_notification
# from notification.models import PushNotificationSubscriber


# @method_decorator(csrf_exempt, name="dispatch")
# class PushNotificationSubscribeView(View):
#     def post(self, request, *args, **kwargs):
#         try:
#             data = json.loads(request.body)
#             endpoint = data.get("endpoint")
#             user_id = data.get("user_id")

#             # Save the subscription to your database
#             PushNotificationSubscriber.objects.create(
#                 user_id=user_id, endpoint=endpoint
#             )

#             # Send a push notification to the user
#             send_push_notification(user_id)

#             return JsonResponse({"message": "Subscription saved successfully."})
#         except Exception as e:
#             return JsonResponse({"error": "An error occurred.", "details": str(e)})


# def send_push_notification(user_id):
#     user_subscriptions = PushNotificationSubscriber.objects.filter(user_id=user_id)
#     payload = {
#         "title": "Notification Title",
#         "body": "Notification Body test",
#     }

#     print(" =============================== ")

#     for subscription in user_subscriptions:
#         # send_user_notification(
#         #     user=subscription.user,
#         #     payload=payload,
#         #     ttl=1000,
#         # )
#         print("/////////////////////////////////////////")


from firebase_admin.messaging import Message, Notification
from fcm_django.models import FCMDevice


def sendMessage():
    Message(
        notification=Notification(title="title", body="text", image="url"),
        topic="Optional topic parameter: Whatever you want",
    )

    device = FCMDevice.objects.all()
    device.send_message(Message)
