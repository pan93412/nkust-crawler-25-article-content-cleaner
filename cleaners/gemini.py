import datetime
import logging
import os
from google import genai
from cleaners.cleaner import Cleaner
from google.genai import types
from models import ArticleMongoModel, CleanedArticleMongoModel


SYSTEM_PROMPT = """Your task is to clean and format the provided text by:

1. Removing metadata elements:
   - Publication timestamps
   - Platform identifiers (e.g., \"發信站\", \"看板\", \"作者\")
   - Source attribution tags (e.g., \"[NOWnews今日新聞]\", \"〔即時新聞／綜合報導〕\")

2. Eliminating supplementary content:
   - \"查看原文\" links
   - \"相關報導\" / \"更多報導\" sections
   - Recommended article lists
   - URLs and hyperlinks
   - Social media sharing buttons/text
   - Advertisement markers
   - Image Figure Caption   

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
Do not translate or provide other information else than the article itself."""


class GeminiCleaner(Cleaner):
    def __init__(self):
        self.client = genai.client.AsyncClient(
            genai.client.BaseApiClient(
                api_key=os.environ.get("GEMINI_API_KEY"),
            )
        )

    async def clean_article(
        self, article: ArticleMongoModel
    ) -> CleanedArticleMongoModel:
        assert "_id" in article, "Article must have an _id"

        generate_content_config = types.GenerateContentConfig(
            response_mime_type="text/plain",
            system_instruction=SYSTEM_PROMPT,
        )

        logging.info(
            f"Cleaning article {article['_id']} with Gemini: {article['content']}"
        )

        response = await self.client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=article["content"],
            config=generate_content_config,
        )

        if response.text is None:
            raise ValueError("Response text is None")

        logging.info(f"Cleaned article {article['_id']} with Gemini: {response.text}")

        return CleanedArticleMongoModel(
            article_id=article["_id"],
            model_name="gemini-2.0-flash-lite",
            content=response.text,
            created_at=datetime.datetime.now(),
        )
