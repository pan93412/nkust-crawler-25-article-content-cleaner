from datetime import datetime
from typing import NotRequired, TypedDict
from bson import ObjectId

class ArticleMongoModel(TypedDict):
    _id: NotRequired[ObjectId]
    article_id: str
    url: str
    title: str
    created_at: datetime
    content: str


class CleanedArticleMongoModel(TypedDict):
    _id: NotRequired[ObjectId]
    article_id: ObjectId
    model_name: str
    content: str
    created_at: datetime
