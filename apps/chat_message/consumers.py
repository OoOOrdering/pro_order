import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # 예시: message, read, typing 등 이벤트 분기
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "event": data.get("event"),
                "message": data.get("message"),
                "user": data.get("user"),
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))
