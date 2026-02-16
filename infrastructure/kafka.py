import json

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

from config import config


class KafkaManager:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None  # Не создаем сразу

    async def start(self):
        # Создаем объект только здесь, когда цикл событий уже запущен
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send_log(self, topic: str, data: dict):
        if not self.producer:
            raise RuntimeError("KafkaProducer is not started. Call start() first.")
        await self.producer.send_and_wait(topic, data)

    async def consume_answers(self, topic: str):
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id="bot_group",
            auto_offset_reset='earliest',
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        await consumer.start()
        try:
            async for msg in consumer:
                yield msg.value
        finally:
            await consumer.stop()


kafka_client = KafkaManager(bootstrap_servers=config.kafka_url)
