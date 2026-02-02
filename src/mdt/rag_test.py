import argparse
import asyncio
import json
import random
from pathlib import Path

from autogen_agentchat.messages import UserMessage

from src.backend import get_client
from src.json_schema import RAG_TEST_JSON_SCHEMA
from src.mdt.ragtool import hybrid_search_answer
from src.prompt.rag_test_prompt import RAG_TEST_PROMPT


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--data_path', type=str, default='data/knowledge_base/chief_expert/')
    parser.add_argument('--count', type=int, default=1000)
    parser.add_argument('--max_concurrency', type=int, default=32, help='Total concurrent LLM requests.')
    args = parser.parse_args()

    random.seed(args.seed)
    client = get_client('gpt-4o')

    # 读取 data_path 里的所有 .txt 文件
    data_dir = Path(args.data_path)
    text_files = list(data_dir.glob('*.txt'))
    documents = []
    for file_path in text_files:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()
            documents.append({'source': str(file_path), 'lines': content.split('。')})

    sem = asyncio.Semaphore(args.max_concurrency)

    async def rate_one(query: str, retrieved_context: dict) -> dict:
        # 全局限流：防止并发爆炸
        async with sem:
            result = await client.create(
                messages=[
                    UserMessage(
                        content=RAG_TEST_PROMPT.format(query=query, retrieved_context=retrieved_context),
                        source="User"
                    )
                ],
                json_output=RAG_TEST_JSON_SCHEMA,
            )
        return json.loads(result.content)

    async def eval_one_query(query: str) -> tuple[int, int, int]:
        """
        返回：relevance_sum, turns
        """
        responses = hybrid_search_answer(query)

        # 内层并行：同一个 query 下，对每个 response 并行打分
        tasks = [asyncio.create_task(rate_one(query, r["content"])) for r in responses]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        rel = turns = 0
        for r in results:
            if isinstance(r, Exception):
                # 你也可以 logger.warning(r) 并跳过
                continue
            rel += int(r.get("relevance_score", 0))
            turns += 1
        return rel, turns

    # 外层并行：count 个 query 一起跑
    queries = [random.choice(random.choice(documents)['lines']) for _ in range(args.count)]
    query_tasks = [asyncio.create_task(eval_one_query(q)) for q in queries]
    query_results = await asyncio.gather(*query_tasks, return_exceptions=True)

    relevance_score = 0
    turns = 0
    for item in query_results:
        if isinstance(item, Exception):
            continue
        rel, t = item
        relevance_score += rel
        turns += t

    print(f"Average Relevance Score: {relevance_score / turns:.2f}")


if __name__ == '__main__':
    asyncio.run(main())
