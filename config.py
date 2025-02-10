import ssl

import pika
from dotenv import load_dotenv
import os
from urllib.parse import urlparse

load_dotenv()

class Config:
    # RabbitMQ
    RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/%2F')
    RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'FORM_QUEUE_SERVICE')
    RABBITMQ_EXCHANGE = os.getenv('RABBITMQ_EXCHANGE', '')
    RABBITMQ_ROUTING_KEY = os.getenv('RABBITMQ_ROUTING_KEY', 'FORM_QUEUE_SERVICE')
    
    # CapSolver
    CAPSOLVER_API_KEY = os.getenv('CAPSOLVER_API_KEY')
    CAPSOLVER_WEBSITE_KEY = os.getenv('CAPSOLVER_WEBSITE_KEY')

    # Max workers
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 1))

    # Form
    FORM_URL = os.getenv('FORM_URL')
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', 2))

    # Browser
    BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true'
    BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', 30000))

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'form_automation.log')

    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:3000')

    @classmethod
    def get_rabbitmq_params(cls):
        """Parse AMQP URL and return connection parameters"""
        url = urlparse(cls.RABBITMQ_URL)
        return {
            'host': url.hostname,
            'port': 5672,
            'virtual_host': url.path[1:],
            'credentials': pika.PlainCredentials(url.username, url.password),
            'ssl_options': None
        }