import dataclasses
from asyncio import Semaphore

import pika
import json
import logging
import asyncio
import aiohttp
import sys

from config import Config
from form_selenium import automate_form_fill_new, FormData


logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

BACKEND_URL = Config.BACKEND_URL

class RabbitMQConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = Config.RABBITMQ_QUEUE
        self.connect()
        self.semaphore = Semaphore(Config.MAX_WORKERS)

    def connect(self):
        try:
            parameters = pika.ConnectionParameters(
                **Config.get_rabbitmq_params(),
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            self.channel.exchange_declare(
                exchange='retry_exchange',
                exchange_type='direct',
                durable=True
            )

            queue_args = {
                'x-dead-letter-exchange': 'retry_exchange',
                'x-dead-letter-routing-key': 'retry'
            }

            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments=queue_args
            )
            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def fetch_form_data(self, form_id: str) -> dict:
        headers = {
            'x-api-key': 'titanicwaslostinthebeach'
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{BACKEND_URL}/submission/{form_id}/") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to fetch form data: {response.status}")

    async def fetch_form_status_complete(self, form_id: str) -> bool:
        headers = {
            'x-api-key': 'titanicwaslostinthebeach'
        }
        body = {
            "status": "completed"
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.patch(f"{BACKEND_URL}/submission/{form_id}/status", json=body) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('status') == 'completed'
                else:
                    print(response)
                    raise Exception(f"Failed to fetch form data: {response.status}")

    async def process_form(self, form_id: str, retry_count: int):

        try:
            form_data = await self.fetch_form_data(form_id)

            non_form_fields =['status', 'error', 'retryAtempts', 'createdAt', 'updatedAt']
            cleaned_data = {k: v
            for k, v in form_data.items() if k not in non_form_fields}
            cleaned_data = self.convert_keys(cleaned_data)
            form_data_instance = FormData( ** cleaned_data)
            await automate_form_fill_new(form_data_instance)
            await self.fetch_form_status_complete(form_id)

        except Exception as e:
            logger.error("we failed submission")
            raise e


    async def process_form_with_limit(self, form_id, retry_count):
        async with self.semaphore:
            await self.process_form(form_id, retry_count)

    @staticmethod
    def convert_keys(data):
        return {
            "send_notice_to_author": data.get("sendNoticeToAuthor"),
            "country_of_residence": data.get("countryOfResidence"),
            "is_child_abuse_content": data.get("isChildAbuseContent"),
            "remove_child_abuse_content": data.get("removeChildAbuseContent"),
            "full_legal_name": data.get("fullLegalName"),
            "company_name": data.get("CompanyName"),
            "company_you_represent": data.get("CompanyYouRepresent"),
            "email": data.get("email"),
            "infringing_urls": data.get("InfringingUrls"),
            "is_related_to_media": data.get("isRelatedToMedia"),
            "question_one": data.get("QuestionOne"),
            "question_two": data.get("QuestionTwo"),
            "question_three": data.get("QuestionThree"),
            "confirm_form": data.get("confirmForm"),
            "signature": data.get("signature"),
            "id": data.get("id"),
        }
    def process_message(self, ch, method, properties, body):
        retry_count = properties.headers.get('retry_count', 0)
        try:
            message = json.loads(body)
            form_id = message.get('data', {}).get('id')

            if not form_id:
                raise ValueError("No form ID in message")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            loop.run_until_complete(self.process_form_with_limit(form_id, retry_count))
            loop.close()

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Successfully processed form {form_id}")

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            if retry_count < Config.MAX_RETRIES:
                # Requeue the message for retry
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            else:
                # Message exceeded retries - reject without requeuing
                # It will go to the dead letter exchange if configured
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start_consuming(self):
        try:
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.process_message
            )
            logger.info("Started consuming messages")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Error in message consumption: {str(e)}")
            if self.connection and not self.connection.is_closed:
                self.connection.close()


if __name__ == "__main__":
    try:
        consumer = RabbitMQConsumer()
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Shutting down consumer")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
    # con = RabbitMQConsumer()
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    #
    # loop.run_until_complete(con.fetch_form_status_complete("7b747b4b-80e5-4b86-bcdd-c6bd2a4def31"))
    # loop.close()

