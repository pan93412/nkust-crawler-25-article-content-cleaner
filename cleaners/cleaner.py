from abc import abstractmethod

from models import ArticleMongoModel, CleanedArticleMongoModel


class Cleaner:
    @abstractmethod
    async def clean_article(
        self, article: ArticleMongoModel
    ) -> CleanedArticleMongoModel:
        pass
