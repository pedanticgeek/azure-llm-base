import os
import openai


class OpenAIConfig:
    # OpenAI services
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    OPENAI_ORG_ID = os.environ["OPENAI_ORG_ID"]
    EMB_MODEL_NAME = os.environ["EMB_MODEL_NAME"]
    CHATGPT_MODEL = os.environ["CHATGPT_MODEL"]
    CHATGPT_VISION_MODEL = os.environ["CHATGPT_VISION_MODEL"]

    def __init__(self) -> None:
        openai.api_type = "openai"
        openai.api_key = self.OPENAI_API_KEY
        openai.organization = self.OPENAI_ORG_ID
        self.client = openai.OpenAI()
        self.aclient = openai.AsyncOpenAI()
