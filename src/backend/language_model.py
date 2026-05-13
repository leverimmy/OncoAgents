import ast
import json
import os
from time import sleep

from dotenv import load_dotenv
from openai import OpenAI

from src.utils import logger

load_dotenv()

LOCAL_BASE_MODELS =  ["Henrychur/MMedS-Llama-3-8B"]

class LanguageModel:
    def __init__(self, model_name: str, url: str | None):
        if model_name in ["Qwen/Qwen3-8B", "Qwen/Qwen3-8B-SFT", "Qwen/Qwen3-8B-DPO", "Henrychur/MMedS-Llama-3-8B"] and (url is not None):
            self.client = OpenAI(
                api_key="0",
                base_url=url,
            )
        elif model_name in ["deepseek-ai/DeepSeek-V3.2", "deepseek-ai/DeepSeek-R1", "Pro/zai-org/GLM-4.7", "Pro/zai-org/GLM-5"]:
            self.client = OpenAI(
                api_key=os.getenv("SILICON_FLOW_API_KEY"),
                base_url=os.getenv("SILICON_FLOW_API_BASE_URL"),
            )
        elif model_name in ["Baichuan-M3-Plus", "Baichuan-M2", "Baichuan-M2-Plus", "Baichuan-M3"]:
            self.client = OpenAI(
                api_key=os.getenv("BAICHUAN_API_KEY"),
                base_url=os.getenv("BAICHUAN_API_BASE_URL"),
            )
        else:
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_API_BASE_URL"),
            )
        self.model_name = model_name
        self.suffix = ""
        if model_name in ["Qwen/Qwen3-8B-No-Thinking"]:
            self.model_name = "qwen3-8b"
            self.suffix = "/no_think"
        else:
            self.suffix = ""
    
    def chat(self, prompt: str, json_format: bool) -> dict | str:
        if json_format:
            cnt = 0
            while True:
                cnt += 1
                try:
                    
                    if self.model_name in LOCAL_BASE_MODELS:
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[{"role": "user", "content": f"{prompt}{self.suffix}"}],
                            max_tokens=1000,
                        )
                        content = response.choices[0].message.content
                    else:
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[{"role": "user", "content": f"{prompt}{self.suffix}"}],
                        )
                        content = response.choices[0].message.content

                    think_content = ""
                    if "</think>" in content:
                        think_content = content.split("<think>")[1].split("</think>")[0].strip()
                        content = content.split("</think>")[1].strip()
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    fixed = content.replace("'", '"')
                    json_result = json.loads(fixed)
                    # if len(think_content) > 0:
                    #     json_result["analysis"] = think_content
                    return json_result
                except Exception as e:
                    logger.error(f"Error during LLM call: {e}")
                    logger.error(f"prompt = {prompt}")
                    if cnt >= 5:
                        return {}
                    logger.info(f"Retrying LLM call, sleep time: {2 ** cnt - 1} seconds")
                    sleep(2 ** cnt - 1)
        else:
            cnt = 0
            while True:
                cnt += 1
                try:
                    if self.model_name in LOCAL_BASE_MODELS:
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[{"role": "user", "content": f"{prompt}{self.suffix}"}],
                            max_tokens=1000,
                        )
                        content = response.choices[0].message.content
                    else:
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[{"role": "user", "content": f"{prompt}{self.suffix}"}],
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
