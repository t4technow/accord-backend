from rest_framework.generics import CreateAPIView
from .serializers import postSerializer
from .models import post
# Create your views here.

class PostCreate(CreateAPIView):
    queryset = post.objects.all()
    serializer_class = postSerializer
