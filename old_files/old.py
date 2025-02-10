import pika
import json
import logging
import time
import ssl
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any
from playwright.async_api import async_playwright
from dataclasses import dataclass
from retry import retry
import sys
import os
from urllib.parse import urlparse
from config import Config

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class FormData:
    """Data structure for form fields"""
    id: str
    countryOfResidence: str
    fullLegalName: str
    CompanyName: str
    CompanyYouRepresent: str
    email: str
    InfringingUrls: list
    isRelatedToMedia: bool
    QuestionOne: str
    QuestionTwo: str
    QuestionThree: str
    confirmForm: bool
    signature: str
    status: str = None
    error: str = None
    retryAtempts: int = None
    createdAt: str = None
    updatedAt: str = None


class FormAutomation:
    def __init__(self, page):
        self.page = page
        self.form_url = Config.FORM_URL

    async def navigate_to_form(self):
        try:
            await self.page.goto(self.form_url, wait_until="networkidle")
            logger.info("Successfully navigated to form page")
        except Exception as e:
            logger.error(f"Failed to navigate to form page: {str(e)}")
            raise

    @retry(tries=3, delay=2)
    async def fill_form(self, data: FormData):
        try:
            await self.page.select_option('select#market_residence', data.countryOfResidence)
            await self.page.fill('#full_name', data.fullLegalName)
            await self.page.fill('#companyname', data.CompanyName)
            await self.page.fill('#representedrightsholder', data.CompanyYouRepresent)
            await self.page.fill('#contact_email_noprefill', data.email)

            for i, url in enumerate(data.InfringingUrls):
                if i == 0:
                    await self.page.fill('#url_box3', url)
                else:
                    await self.page.click('text=Add additional field')
                    await self.page.fill(f'#url_box3_{i + 1}', url)

            if data.isRelatedToMedia:
                await self.page.click('#is_geo_ugc_imagery--yes')
            else:
                await self.page.click('#is_geo_ugc_imagery--no')

            await self.page.fill('#legalother_explain_googlemybusiness_not_germany', data.QuestionOne)
            await self.page.fill('#legalother_quote', data.QuestionTwo)
            await self.page.fill('#legalother_quote_googlemybusiness_not_germany', data.QuestionThree)

            if data.confirmForm:
                await self.page.check('#legal_consent_statement--agree')

            await self.page.fill('#signature', data.signature)

            logger.info(f"Successfully filled form for ID: {data.id}")

        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            raise

    async def submit_form(self):
        try:
            await self.page.click('button.submit-button')
            await self.page.wait_for_selector('.confirmation-message:not(.hidden)', timeout=10000)
            logger.info("Form submitted successfully")
            return True
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            raise


class RabbitMQConsumer:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue_name = Config.RABBITMQ_QUEUE
        self.connect()

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
            async with session.get(f"http://localhost:3000/submission/{form_id}/") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"Failed to fetch form data: {response.status}")

    async def process_form(self, form_id: str, retry_count: int):
        form_data = await self.fetch_form_data(form_id)

        non_form_fields = ['status', 'error', 'retryAtempts', 'createdAt', 'updatedAt']
        cleaned_data = {k: v for k, v in form_data.items() if k not in non_form_fields}

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=Config.BROWSER_HEADLESS)
            context = await browser.new_context()
            page = await context.new_page()

            form_automation = FormAutomation(page)
            form_data_obj = FormData(**cleaned_data)

            await form_automation.navigate_to_form()
            await form_automation.fill_form(form_data_obj)
            await form_automation.submit_form()

            await context.close()
            await browser.close()

    def process_message(self, ch, method, properties, body):
        try:
            message = json.loads(body)
            retry_count = properties.headers.get('retry_count', 0)
            form_id = message.get('data', {}).get('id')

            if not form_id:
                raise ValueError("No form ID in message")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.process_form(form_id, retry_count))
            loop.close()

            ch.basic_ack(delivery_tag=method.delivery_tag)
            logger.info(f"Successfully processed form {form_id}")

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            if retry_count < Config.MAX_RETRIES:
                properties.headers['retry_count'] = retry_count + 1
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queue_name,
                    body=body,
                    properties=properties
                )
            ch.basic_nack(delivery_tag=method.delivery_tag)

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