class ArticleNotFound(ValueError):
    def __init__(self, article_id: str):
        self.article_id = article_id

    def __str__(self):
        return f"Article {self.article_id} not found"


class CleanedArticleNotFound(ValueError):
    def __init__(self, article_id: str):
        self.article_id = article_id

    def __str__(self):
        return f"Cleaned article {self.article_id} not found"
