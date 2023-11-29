import os
from config.azure_config import AzureConfig
from config.api_config import ApiConfig
from config.openai_config import OpenAIConfig
from config.logger import Logger

gpt = OpenAIConfig()
config = ApiConfig()
logger = Logger(
    name=os.getenv("AZURE_ENV_NAME"),
    file=True,
    level=os.getenv("APP_LOG_LEVEL", "INFO"),
)

az = AzureConfig()
