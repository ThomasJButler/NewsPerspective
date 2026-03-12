import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.types import TypeDecorator

from .database import Base


class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_title = Column(Text, nullable=False)
    rewritten_title = Column(Text, nullable=True)
    tldr = Column(Text, nullable=True)
    original_description = Column(Text, nullable=True)
    source_name = Column(String, nullable=True)
    source_id = Column(String, nullable=True)
    author = Column(String, nullable=True)
    url = Column(String, unique=True, nullable=False)
    image_url = Column(String, nullable=True)
    published_at = Column(UTCDateTime(), nullable=True)
    fetched_at = Column(UTCDateTime(), default=lambda: datetime.now(timezone.utc))
    was_rewritten = Column(Boolean, default=False)
    original_sentiment = Column(String, nullable=True)  # positive/neutral/negative
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    is_good_news = Column(Boolean, default=False)
    category = Column(String, nullable=True)
    processing_status = Column(String, default="pending")  # pending/processed/failed
