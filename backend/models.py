from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean
from sqlalchemy.sql import func
from backend.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)
    url = Column(String(1000), nullable=True)
    published_at = Column(DateTime, nullable=True)
    region = Column(String(50), nullable=True)
    theme = Column(String(50), nullable=True)
    country = Column(String(100), nullable=True)
    risk_score = Column(Float, default=0.0)
    sentiment = Column(Float, default=0.0)
    is_breaking = Column(Boolean, default=False)
    raw_source = Column(String(20), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class DailyBrief(Base):
    __tablename__ = "daily_briefs"

    id = Column(Integer, primary_key=True, index=True)
    brief_date = Column(String(10), unique=True, nullable=False)
    executive_summary = Column(Text, nullable=True)
    key_developments = Column(Text, nullable=True)
    threat_assessment = Column(Text, nullable=True)
    outlook = Column(Text, nullable=True)
    total_events = Column(Integer, default=0)
    high_risk_events = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())


class RegionalSummary(Base):
    __tablename__ = "regional_summaries"

    id = Column(Integer, primary_key=True, index=True)
    brief_date = Column(String(10), nullable=False)
    region = Column(String(50), nullable=False)
    summary = Column(Text, nullable=True)
    risk_level = Column(String(20), nullable=True)
    risk_score = Column(Float, default=0.0)
    top_themes = Column(String(200), nullable=True)
    event_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
