import logging
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

from cleaners.cleaner import Cleaner
from exceptions import ArticleNotFound, CleanedArticleNotFound
from models import ArticleMongoModel, CleanedArticleMongoModel


class CleanedArticleProcessor:
    def __init__(self, mongo_client: AsyncMongoClient, cleaner: Cleaner, platform: str):
        self.mongo_client = mongo_client
        self.cleaner = cleaner
        self.platform = platform

    async def clean_article(self, article_id: str) -> None:
        platform_database = self.mongo_client[self.platform]
        collection: AsyncCollection[ArticleMongoModel] = platform_database["articles"]
        cleaned_collection = platform_database["articles_cleaned"]

        article = await collection.find_one({"article_id": article_id})
        if not article:
            raise ArticleNotFound(article_id)

        assert "_id" in article, "Article must have an _id"

        logging.info(f"Cleaning article {article_id} ({article['_id']}")
        cleaned_article = await self.cleaner.clean_article(article)
        await cleaned_collection.insert_one(cleaned_article)


    async def get_cleaned_article(self, article_id: str) -> CleanedArticleMongoModel | None:
        platform_database = self.mongo_client[self.platform]
        cleaned_collection = platform_database["articles_cleaned"]

        cleaned_article = await cleaned_collection.find_one({"article_id": article_id})
        return cleaned_article
