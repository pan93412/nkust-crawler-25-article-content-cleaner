import asyncio
import logging
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
        cleaned_collection: AsyncCollection[CleanedArticleMongoModel] = platform_database["cleaned_articles"]

        article = await collection.find_one({"article_id": article_id})
        if not article:
            raise ArticleNotFound(article_id)

        assert "_id" in article, "Article must have an _id"

        logging.info(f"Cleaning article {article_id} ({article['_id']}")
        cleaned_article = await self.cleaner.clean_article(article)

        await cleaned_collection.insert_one(cleaned_article)


    async def get_cleaned_article(self, article_id: str) -> CleanedArticleMongoModel | None:
        platform_database = self.mongo_client[self.platform]
        cleaned_collection: AsyncCollection[CleanedArticleMongoModel] = platform_database["cleaned_articles"]

        cleaned_article = await cleaned_collection.find_one({"article_id": article_id})
        return cleaned_article

    async def clean_all_articles(self) -> None:
        platform_database = self.mongo_client[self.platform]
        collection: AsyncCollection[ArticleMongoModel] = platform_database["articles"]
        
        tasks = []

        async for article in collection.find():
            assert "_id" in article, "Article must have an _id"

            cleaned_article = await self.get_cleaned_article(article["article_id"])
            if cleaned_article:
                logging.info(f"Article {article['article_id']} already cleaned")
                continue

            tasks.append(self.clean_article(article["article_id"]))

        await asyncio.gather(*tasks)
