import re
from typing import TypedDict, Literal, NotRequired
from datetime import datetime
from bson import ObjectId
import emoji

from cleaners.cleaner import Cleaner
from models import CleanedArticleMongoModel

class ArticleMongoModel(TypedDict):
    _id: NotRequired[ObjectId]
    article_id: str
    url: str
    title: str
    created_at: datetime
    content: str

class CommentMongoModel(TypedDict):
    _id: NotRequired[ObjectId]
    article_id: ObjectId
    comment_id: str  # index (article_id, comment_id)
    content: str
    created_at: datetime
    author: str
    likes: int | None
    dislikes: int | None
    reaction_type: Literal["+1", "-1", "0"] | None

class ReplyMongoModel(TypedDict):
    _id: NotRequired[ObjectId]
    article_id: ObjectId
    comment_id: ObjectId
    reply_id: str  # index (article_id, comment_id, reply_id)
    content: str
    created_at: datetime
    author: str
    likes: int | None
    dislikes: int | None
    reaction_type: Literal["+1", "-1", "0"] | None

class BasicCleaner(Cleaner):
    def __init__(self):
        # Patterns for cleaning
        self.separator_pattern = re.compile(r'^\s*(?:-{3,}|⸻+)\s*$', re.MULTILINE)
        self.html_tag_pattern = re.compile(r'<[^>]+>')
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        
        # Pattern for figure captions like "▲川普上台後，其家族光靠加密幣就進帳高達323億。（圖／翻攝自川普臉書）"
        self.figure_caption_pattern = re.compile(r'▲[^。]*。（[^）]*）')
        
        # Pattern for related news sections
        self.related_news_patterns = [
            re.compile(r'更多.*報導.*', re.DOTALL),
            re.compile(r'看更多相關新聞.*', re.DOTALL),
            re.compile(r'相關報導.*', re.DOTALL),
            re.compile(r'延伸閱讀.*', re.DOTALL)
        ]
        
        # Pattern for PTT metadata
        self.ptt_metadata_pattern = re.compile(
            r'--\s*\n'
            r'※\s+發信站:.*?\n'
            r'(?:※\s+文章網址:.*?\n)?'
            r'(?:※\s+編輯:.*?\n)*', 
            re.DOTALL
        )

    def remove_emojis(self, text: str) -> str:
        """Remove emojis from text"""
        return emoji.replace_emoji(text, '')

    def remove_separators(self, text: str) -> str:
        """Remove unnecessary separators like '---' from text"""
        return self.separator_pattern.sub(r'', text)

    def remove_html_and_urls(self, text: str) -> str:
        """Remove HTML tags and URLs from text"""
        text = self.html_tag_pattern.sub(r'', text)
        return self.url_pattern.sub(r'', text)

    def remove_figure_captions(self, text: str) -> str:
        """Remove figure captions"""
        return self.figure_caption_pattern.sub(r'', text)

    def remove_related_news(self, text: str) -> str:
        """Remove sections that begin with phrases like '更多...報導', '看更多相關新聞', etc."""
        for pattern in self.related_news_patterns:
            text = pattern.sub(r'', text)
        return text

    def remove_ptt_metadata(self, text: str) -> str:
        """Remove PTT metadata"""
        return self.ptt_metadata_pattern.sub(r'', text)
    
    def remove_sources(self, text: str) -> str:
        """Remove sources"""
        text = re.sub(r'^來源：.*', '', text)
        text = re.sub(r'^文章撰文者｜.*', '', text)
        text = re.sub(r'^文章出處：.*', '', text)
        text = re.sub(r'By[—\-:]+.*', '', text)
        return text
    
    def remove_other_links(self, text: str) -> str:
        """Remove other links"""

        text = text.replace("Instagram photos and videos", "")
        text = re.sub(r'Instagram \(.*?\)', '', text)
        text = text.replace("(?:更多資訊|最新時事觀點)歡迎.+", "")
        text = text.replace("如果你喜歡這種.*的深度分析，也歡迎留言告訴我你還想知道什麼。", "")
        text = re.sub(r'記者(.+)\s*[／/].*報導', '', text)

        return text
        
    def clean_text(self, text: str) -> str:
        """Apply all cleaning operations to text"""
        if not text:
            return ""
            
        text = self.remove_emojis(text)
        text = self.remove_separators(text)
        text = self.remove_html_and_urls(text)
        text = self.remove_figure_captions(text)
        text = self.remove_related_news(text)
        text = self.remove_ptt_metadata(text)
        text = self.remove_sources(text)
        text = self.remove_other_links(text)
        
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = text.strip()
        
        return text

    async def clean_article(
        self, article: ArticleMongoModel
    ) -> CleanedArticleMongoModel:
        assert "_id" in article, "Article must have an _id"

        return CleanedArticleMongoModel(
            article_id=article["_id"],
            content=self.clean_text(article["content"]),
            created_at=article["created_at"],
            model_name="basic",
        )
