import json
from collections.abc import AsyncGenerator
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from config import config


class KafkaManager:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
        await self.producer.start()

    async def stop(self) -> None:
        if self.producer is not None:
            await self.producer.stop()

    async def send_message(self, topic: str, data: dict[str, Any]) -> None:
        if self.producer is None:
            raise RuntimeError("KafkaProducer is not started. Call start() first.")
        await self.producer.send_and_wait(topic, data)

    async def consume_topic(self, topic: str) -> AsyncGenerator[dict[str, Any], None]:
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id="bot_group",
            auto_offset_reset="earliest",
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        )
        await consumer.start()
        try:
            async for message in consumer:
                yield message.value
        finally:
            await consumer.stop()


kafka_client = KafkaManager(bootstrap_servers=config.kafka_url)
