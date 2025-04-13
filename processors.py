import asyncio
import logging
import os
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

from cleaners.cleaner import Cleaner
from exceptions import ArticleNotFound
from models import ArticleMongoModel, CleanedArticleMongoModel


class CleanedArticleProcessor:
    def __init__(self, mongo_client: AsyncMongoClient, cleaner: Cleaner, platform: str):
        self.mongo_client = mongo_client
        self.cleaner = cleaner
        self.platform = platform

    async def clean_article(self, article_id: str) -> None:
        platform_database = self.mongo_client[self.platform]
        collection: AsyncCollection[ArticleMongoModel] = platform_database["articles"]
        cleaned_collection: AsyncCollection[CleanedArticleMongoModel] = (
            platform_database["cleaned_articles"]
        )

        article = await collection.find_one({"article_id": article_id})
        if not article:
            raise ArticleNotFound(article_id)

        assert "_id" in article, "Article must have an _id"

        logging.info(f"Cleaning article {article_id} ({article['_id']})")
        cleaned_article = await self.cleaner.clean_article(article)

        await cleaned_collection.insert_one(cleaned_article)

    async def get_cleaned_article(
        self, article_id: str
    ) -> CleanedArticleMongoModel | None:
        platform_database = self.mongo_client[self.platform]

        article_collection: AsyncCollection[ArticleMongoModel] = platform_database[
            "articles"
        ]
        cleaned_collection: AsyncCollection[CleanedArticleMongoModel] = (
            platform_database["cleaned_articles"]
        )

        article = await article_collection.find_one({"article_id": article_id})
        if not article:
            raise ArticleNotFound(article_id)

        assert "_id" in article, "Article must have an _id"

        cleaned_article = await cleaned_collection.find_one(
            {"article_id": article["_id"]}, sort=[("created_at", -1)]
        )
        return cleaned_article

    async def clean_all_articles(self) -> None:
        platform_database = self.mongo_client[self.platform]
        collection: AsyncCollection[ArticleMongoModel] = platform_database["articles"]

        semaphore = asyncio.Semaphore(int(os.getenv("CLEANER_CONCURRENCY", 10)))

        async def clean_article_with_semaphore(article_id: str) -> None:
            # check if article is already cleaned
            cleaned_article = await self.get_cleaned_article(article_id)
            if cleaned_article:
                logging.info(f"Article {article_id} already cleaned")
                return

            async with semaphore:
                await self.clean_article(article_id)

        tasks = [
            clean_article_with_semaphore(article["article_id"])
            async for article in collection.find()
        ]
        await asyncio.gather(*tasks)
