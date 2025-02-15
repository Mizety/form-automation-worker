import pika
from dotenv import load_dotenv
import os
from urllib.parse import urlparse

load_dotenv()

class Config:
    # RabbitMQ
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', "2a01:4f8:c17:c966::1")
    RABBITMQ_PORT = os.getenv('RABBITMQ_PORT', "6666")
    RABBITMQ_USERNAME = os.getenv('RABBITMQ_USERNAME', "guest")
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', "guest")
    RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', "/")
    RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'FORM_QUEUE_SERVICE')
    RABBITMQ_EXCHANGE = os.getenv('RABBITMQ_EXCHANGE', '')
    RABBITMQ_ROUTING_KEY = os.getenv('RABBITMQ_ROUTING_KEY', 'FORM_QUEUE_SERVICE')
    
    # CapSolver
    CAPSOLVER_API_KEY = os.getenv('CAPSOLVER_API_KEY')
    CAPSOLVER_WEBSITE_KEY = os.getenv('CAPSOLVER_WEBSITE_KEY')

    # Max workers
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', 2))

    # Form
    FORM_URL = os.getenv('FORM_URL')
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    RETRY_DELAY = int(os.getenv('RETRY_DELAY', 20000))

    # Browser
    BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true'
    BROWSER_TIMEOUT = int(os.getenv('BROWSER_TIMEOUT', 30000))
    VARIANT_GERMANY = os.getenv('VARIANT_GERMANY', 'true').lower() == 'true'
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'form_automation.log')

    BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:3000')

    CAPSOLVER_API_KEY = os.getenv('CAPSOLVER_API_KEY', "") 
    API_KEY = os.getenv('API_KEY', "")

    @classmethod
    def get_rabbitmq_params(cls):
        """Parse AMQP URL and return connection parameters"""
        print(cls.RABBITMQ_HOST)
        print(cls.RABBITMQ_PORT)
        print(cls.RABBITMQ_VHOST)
        return {
            'host': cls.RABBITMQ_HOST,
            'port': cls.RABBITMQ_PORT,
            'virtual_host': cls.RABBITMQ_VHOST,
            'credentials': pika.PlainCredentials(cls.RABBITMQ_USERNAME, cls.RABBITMQ_PASSWORD),
            'ssl_options': None
        }