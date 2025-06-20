import json

from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"notification_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # 예시: 알림 읽음, 구독 등
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "notify",
                "event": data.get("event"),
                "notification": data.get("notification"),
            },
        )

    async def notify(self, event):
        await self.send(text_data=json.dumps(event))
