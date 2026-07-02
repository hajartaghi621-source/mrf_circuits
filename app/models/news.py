"""News articles model for the Laboratory Log section."""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, DateTime
from app.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=True)
    excerpt = Column(String(500), nullable=True)
    link_url = Column(String(500), nullable=True)
    link_label = Column(String(100), nullable=True)  # e.g., "Read Technical Brief", "View Certification"
    published_date = Column(Date, default=date.today)
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NewsArticle {self.title}>"
