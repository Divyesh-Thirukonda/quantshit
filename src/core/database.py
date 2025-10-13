"""
Database models and utilities.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
from src.core.config import get_settings

Base = declarative_base()


class Market(Base):
    """Market model."""
    __tablename__ = "markets"
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)
    market_id = Column(String(100), nullable=False)
    title = Column(String(500), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    yes_price = Column(Float)
    no_price = Column(Float)
    volume = Column(Float, default=0.0)
    open_interest = Column(Float, default=0.0)
    close_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    trades = relationship("Trade", back_populates="market")
    opportunities = relationship("ArbitrageOpportunity", back_populates="market")


class Trade(Base):
    """Trade model."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    strategy_name = Column(String(100), nullable=False)
    platform = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # BUY/SELL
    outcome = Column(String(10), nullable=False)  # YES/NO
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    filled_quantity = Column(Float, default=0.0)
    status = Column(String(20), default="PENDING")  # PENDING/FILLED/CANCELLED/REJECTED
    order_id = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    filled_at = Column(DateTime)
    
    # Relationships
    market = relationship("Market", back_populates="trades")


class ArbitrageOpportunity(Base):
    """Arbitrage opportunity model."""
    __tablename__ = "arbitrage_opportunities"
    
    id = Column(Integer, primary_key=True)
    market_id = Column(Integer, ForeignKey("markets.id"), nullable=False)
    strategy_name = Column(String(100), nullable=False)
    opportunity_type = Column(String(50), nullable=False)  # CROSS_PLATFORM/CORRELATION
    description = Column(Text)
    expected_profit = Column(Float, nullable=False)
    confidence_score = Column(Float, default=0.5)
    status = Column(String(20), default="DETECTED")  # DETECTED/EXECUTED/MISSED/INVALID
    created_at = Column(DateTime, default=func.now())
    executed_at = Column(DateTime)
    
    # Relationships
    market = relationship("Market", back_populates="opportunities")


class Portfolio(Base):
    """Portfolio tracking model."""
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)
    market_id = Column(String(100), nullable=False)
    outcome = Column(String(10), nullable=False)  # YES/NO
    quantity = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    current_price = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class RiskMetrics(Base):
    """Risk metrics tracking."""
    __tablename__ = "risk_metrics"
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    total_exposure = Column(Float, default=0.0)
    daily_pnl = Column(Float, default=0.0)
    var_95 = Column(Float, default=0.0)  # Value at Risk 95%
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    num_positions = Column(Integer, default=0)
    correlation_exposure = Column(Float, default=0.0)


def create_database_engine():
    """Create database engine."""
    settings = get_settings()
    engine = create_engine(settings.database_url, echo=settings.debug)
    return engine


def get_session():
    """Get database session."""
    engine = create_database_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_tables():
    """Create all tables."""
    engine = create_database_engine()
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables."""
    engine = create_database_engine()
    Base.metadata.drop_all(bind=engine)