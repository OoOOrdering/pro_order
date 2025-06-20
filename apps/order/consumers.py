import json

from channels.generic.websocket import AsyncWebsocketConsumer


class OrderStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]
        self.group_name = f"order_{self.order_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # 예시: 주문 상태 변경 이벤트
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "order_status",
                "event": data.get("event"),
                "status": data.get("status"),
            },
        )

    async def order_status(self, event):
        await self.send(text_data=json.dumps(event))
