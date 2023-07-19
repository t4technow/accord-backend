
# custom auth to incude user in scope of aasyncconsumer 

from typing import Any
from channels.db import database_sync_to_async
from urllib.parse import parse_qs
from django.db import close_old_connections
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from channels.auth import AuthMiddlewareStack
import json




@database_sync_to_async
def get_user(token):
    try:
        user = get_user_model().objects.get(id=token['user_id'])
        return user
    except :
        return AnonymousUser()
    


class JwtAuthForAsgi(BaseMiddleware):

    def __init__(self,inner) -> None:
        self.inner = inner

    async def __call__(self, scope,recieve,send) -> Any:
        close_old_connections()
        token = parse_qs(scope['query_string'].decode("utf8"))['token'][0]   

        try:
            UntypedToken(token)
        except (InvalidToken , TokenError) as e:

            response = {'error': 'Invalid token'}
           
            await send({
                'type': 'http.response.start',
                'status': 401,
                'headers': [
                    (b'content-type', b'application/json'),
                ],
            })
            await send({
                'type': 'http.response.body',
                'body': json.dumps(response).encode('utf-8'),
            })
            return 
        else:
            token_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            scope['user'] = await get_user(token_data)

        return await super().__call__(scope,recieve,send)
    
def JwtAuthForAsgiStack(inner):
    return JwtAuthForAsgi(AuthMiddlewareStack(inner))


    