import datetime
import logging
import os
import lmstudio
from lmstudio.history import Chat

from cleaners.cleaner import Cleaner
from models import ArticleMongoModel, CleanedArticleMongoModel


SYSTEM_PROMPT = """Your task is to clean and format the provided text by:

1. Removing metadata elements:
   - Publication timestamps
   - Platform identifiers (e.g., "發信站", "看板", "作者")
   - Source attribution tags (e.g., "[NOWnews今日新聞]", "〔即時新聞／綜合報導〕")

2. Eliminating supplementary content:
   - "查看原文" links
   - "相關報導" sections
   - Recommended article lists
   - URLs and hyperlinks
   - Social media sharing buttons/text
   - Advertisement markers

3. Formatting requirements:
   - Preserve the main article content and title
   - Maintain original paragraph structure
   - Keep relevant image captions if present
   - Retain source attribution in a standardized format at the end (if necessary)

4. Additional cleaning:
   - Remove redundant whitespace and line breaks
   - Standardize punctuation
   - Remove HTML artifacts if present
   - Remove tracking codes and analytics markers
   - No source or any URL about references

Please provide the cleaned text while maintaining its original meaning and essential information.
Do not translate or modify the meaning of the text."""

class Gemma3Cleaner(Cleaner):
    def __init__(self):
        self.lmstudio_client = lmstudio.AsyncClient(os.getenv("LMSTUDIO_API_HOST"))

    async def clean_article(self, article: ArticleMongoModel) -> CleanedArticleMongoModel:
        assert "_id" in article, "Article must have an _id"

        chat = Chat()
        chat.add_system_prompt(SYSTEM_PROMPT)
        chat.add_user_message(article["content"])

        logging.debug(f"Cleaning article {article['_id']}: {article['content']}")

        async with self.lmstudio_client as client:
            llm = await client.llm.model("gemma-3-12b-it")
            response = await llm.respond(chat, config=lmstudio.LlmPredictionConfig(
                temperature=0.3,
                top_k_sampling=100,
                top_p_sampling=0.95,
            ))

        logging.debug(f"Cleaned article {article['_id']} with {llm.identifier}: {response.content}")

        return CleanedArticleMongoModel(
            article_id=article["_id"],
            model_name=llm.identifier,
            content=response.content,
            created_at=datetime.datetime.now(),
        )
