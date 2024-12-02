from channels.generic.websocket import WebsocketConsumer
from django.conf import settings
from accounts.models import User
import jwt
import json

class BaseConsumer(WebsocketConsumer):

    def connect(self):
        token = self.scope["url_route"]["kwargs"]["token"]
        try:
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token["user_id"]
            user = User.objects.get(id=user_id)
            self.accept()
            self.send(text_data=json.dumps({
                'message': f'Welcome to Caelium, {user.username}!'
            }))
        except jwt.ExpiredSignatureError:
            self.close()
        except jwt.DecodeError:
            self.close()
        except User.DoesNotExist:
            self.close()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        pass