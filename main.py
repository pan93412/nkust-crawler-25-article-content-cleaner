import argparse
import asyncio
import logging
import os
from pymongo import AsyncMongoClient

from cleaners.gemma3 import Gemma3Cleaner
from processors import CleanedArticleProcessor


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_mongo_client() -> AsyncMongoClient:
    return AsyncMongoClient(os.getenv("MONGO_URI"))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", type=str, required=True)
    parser.add_argument("--article-id", type=str, required=True)
    args = parser.parse_args()

    mongo_client = get_mongo_client()
    cleaner = Gemma3Cleaner()

    processor = CleanedArticleProcessor(mongo_client, cleaner, args.platform)
    cleaned_article = await processor.clean_article(args.article_id)

    print(cleaned_article)


if __name__ == "__main__":
    asyncio.run(main())
