import dataclasses
from asyncio import Semaphore

import pika
import json
import logging
import asyncio
import aiohttp
import sys

from config import Config
from form_playwright import automate_form_fill_new, FormData
from discord_notification import notify_to_discord

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
                blocked_connection_timeout=3000
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
        
            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True,
            )
            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            raise

    async def fetch_form_data(self, form_id: str) -> dict:
        headers = {
            'x-api-key': Config.API_KEY
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{BACKEND_URL}/submission/{form_id}/") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(response)
                    raise Exception(f"Failed to fetch form data: {response.status}")

    async def fetch_form_status_complete(self, form_id: str, status: str) -> bool:
        headers = {
            'x-api-key': Config.API_KEY
        }
        body = {
            "status": status
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
            await self.fetch_form_status_complete(form_id, "pending")
            non_form_fields =['status', 'error', 'retryAtempts', 'createdAt', 'updatedAt']
            cleaned_data = {k: v
            for k, v in form_data.items() if k not in non_form_fields}
            cleaned_data = self.convert_keys(cleaned_data)
            form_data_instance = FormData( ** cleaned_data)
            await automate_form_fill_new(form_data_instance)
            await self.fetch_form_status_complete(form_id, "completed")

        except Exception as e:
            logger.error("we failed submission")
            try:
                await self.fetch_form_status_complete(form_id, "retry")
            except Exception as status_error:
                logger.error(f"Failed to update status: {status_error}")
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
    
    def on_message_callback_wrapper(self, ch, method, properties, body):
    # Ensure the async processing runs in the event loop
        try:
            asyncio.run(self.process_message(ch, method, properties, body))
        except Exception as e:
            logger.error(f"Error in message consumption: {str(e)}")
            if self.connection and not self.connection.is_closed:
                self.connection.close()

    async def process_message(self, ch, method, properties, body):
        retry_count = properties.headers.get('retry_count', 0)
        message = json.loads(body)
        form_id = message.get('data', {}).get('id')
        try:
        
            if not form_id:
                raise ValueError("No form ID in message")

            await self.process_form_with_limit(form_id, retry_count)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Successfully processed form {form_id}")

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            if retry_count < Config.MAX_RETRIES:
                    # Requeue the message for retry
                    updated_message = json.dumps(message)
                    updated_properties = pika.BasicProperties(
                        headers={'retry_count': retry_count + 1},
                        expiration=str(Config.RETRY_DELAY)
                    )

                    ch.basic_publish(
                        exchange='',
                        routing_key=self.queue_name,
                        body=updated_message,
                        properties=updated_properties
                    )

                    ch.basic_ack(delivery_tag=method.delivery_tag)
            else:
                # Message exceeded retries - reject without requeuing
                logger.error(f"Message exceeded retries - rejecting without requeuing: {str(e)}")
                # Only update status if we have a valid form_id
                if form_id:
                    notify_to_discord(f"Form: {form_id} - Message exceeded retries - rejecting without requeuing",error=str(e),  type = 1)
                    await self.fetch_form_status_complete(form_id, "failed")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    async def start_consuming(self):
        try:
            loop = asyncio.get_event_loop()
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=self.on_message_callback_wrapper
            )
            await loop.run_in_executor(None, self.channel.start_consuming)
            logger.info("Started consuming messages")
            # self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Error in message consumption: {str(e)}")
            if self.connection and not self.connection.is_closed:
                self.connection.close()
    async def start_async_consuming(self):
        try:
            await self.start_consuming()
        except Exception as e:
            logger.error(f"Error in async consumption: {str(e)}")
            if self.connection and not self.connection.is_closed:
                self.connection.close()

if __name__ == "__main__":
    try:
        notify_to_discord("Starting consumer",  type = 1)
        consumer = RabbitMQConsumer()
        asyncio.run(consumer.start_async_consuming())
    except KeyboardInterrupt:
        logger.info("Shutting down consumer")
        notify_to_discord("Shutting down consumer",  type = 1)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        notify_to_discord(f"Fatal error: {str(e)}",error=str(e),  type = 1)
        sys.exit(1)
    # con = RabbitMQConsumer()
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    #
    # loop.run_until_complete(con.fetch_form_status_complete("7b747b4b-80e5-4b86-bcdd-c6bd2a4def31"))
    # loop.close()

