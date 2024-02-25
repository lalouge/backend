from accounts.models.users import User

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

import json


class DeviceConsumer(AsyncWebsocketConsumer):

    @sync_to_async
    def get_user_id(self, user_query_id):
        try:
            user_instance = User.get_user(query_id=user_query_id)
        except:
            return None
        
        return user_instance.pk

    async def connect(self):
        user_query_id = self.scope['url_route']['kwargs']['user_query_id']
        
        user_id = await self.get_user_id(user_query_id=user_query_id)

        print("USER_ID::: ", user_id)

        # Use user_id as needed for your logic
        await self.accept()

        # Connect to a unique channel based on the user ID
        await self.channel_layer.group_add(
            f"user_{user_id}",
            self.channel_name
        )

    async def disconnect(self, close_code):
        user_query_id = self.scope['url_route']['kwargs']['user_query_id']

        user_id = await self.get_user_id(user_query_id=user_query_id)

        print("USER ID IS::: ", user_id)
        # Use user_id as needed for your logic
        # Disconnect from the unique channel when the WebSocket is closed
        await self.channel_layer.group_discard(
            f"user_{user_id}",
            self.channel_name
        )

    async def send_device_data(self, event):
        device_data = event['device_data']
        await self.send(text_data=json.dumps({'device_data': device_data}))