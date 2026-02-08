import json
import os
from time import sleep

from dotenv import load_dotenv
from openai import OpenAI

from src.utils import logger

load_dotenv()


class LanguageModel:
    def __init__(self, model_name: str, url: str | None):
        if model_name in ["Qwen/Qwen3-8B"] and (url is not None):
            self.client = OpenAI(
                api_key="0",
                base_url=url,
            )
        else:
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_API_BASE_URL"),
            )
        self.model_name = model_name
    
    def chat(self, prompt: str, json_format: bool) -> dict | str:
        if json_format:
            cnt = 0
            while True:
                cnt += 1
                try:
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                    )
                    content = response.choices[0].message.content
                    if "</think>" in content:
                        content = content.split("</think>")[1].strip()
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    return json.loads(content)
                except Exception as e:
                    logger.error(f"Error during LLM call: {e}")
                    if cnt >= 5:
                        return {}
                    logger.info(f"Retrying LLM call, sleep time: {2 ** cnt - 1} seconds")
                    sleep(2 ** cnt - 1)
        else:
            cnt = 0
            while True:
                cnt += 1
                try:
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                    )
                    content = response.choices[0].message.content
                    if "</think>" in content:
                        content = content.split("</think>")[1].strip()
                    return content
                except Exception as e:
                    logger.error(f"Error during LLM call: {e}")
                    if cnt >= 5:
                        return {}
                    logger.info(f"Retrying LLM call, sleep time: {2 ** cnt - 1} seconds")
                    sleep(2 ** cnt - 1)
