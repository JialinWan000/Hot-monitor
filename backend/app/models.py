"""SQLAlchemy 数据模型 - 使用 SQLAlchemy 2.1 Mapped 类型注解"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Boolean, Integer, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Keyword(Base):
    """关键词表 - 用户监控的关键词"""
    __tablename__ = "keywords"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(50))  # 分类：AI、编程、科技等
    priority: Mapped[str] = mapped_column(String(20), default="normal")  # 优先级：low/normal/high/critical
    description: Mapped[Optional[str]] = mapped_column(String(500))  # 关键词描述说明
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # 关联的热点
    hotspots: Mapped[List["Hotspot"]] = relationship(
        "Hotspot",
        secondary="keyword_hotspot",
        back_populates="keywords"
    )
    
    def __repr__(self) -> str:
        return f"Keyword(id={self.id}, keyword='{self.keyword}')"


class Hotspot(Base):
    """热点表 - 发现的热点内容"""
    __tablename__ = "hotspots"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)  # AI生成的摘要
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # 来源平台
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))
    
    # AI分析结果
    score: Mapped[Optional[float]] = mapped_column(Float)  # AI评分 0-100
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)  # AI验证真实性
    is_fake: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否为假消息
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text)  # AI分析详情
    tags: Mapped[Optional[str]] = mapped_column(JSON)  # AI生成的标签
    
    # 状态
    notified: Mapped[bool] = mapped_column(Boolean, default=False)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # 时间戳
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)  # 原文发布时间
    discovered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    # 关联的关键词
    keywords: Mapped[List["Keyword"]] = relationship(
        "Keyword",
        secondary="keyword_hotspot",
        back_populates="hotspots"
    )
    
    # 关联的通知
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="hotspot",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"Hotspot(id={self.id}, title='{self.title[:30]}...')"


class KeywordHotspot(Base):
    """关键词-热点关联表"""
    __tablename__ = "keyword_hotspot"
    
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), primary_key=True)
    hotspot_id: Mapped[int] = mapped_column(ForeignKey("hotspots.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Notification(Base):
    """通知记录表"""
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hotspot_id: Mapped[int] = mapped_column(ForeignKey("hotspots.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # push/email
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/sent/failed
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # 关联热点
    hotspot: Mapped["Hotspot"] = relationship("Hotspot", back_populates="notifications")
    
    def __repr__(self) -> str:
        return f"Notification(id={self.id}, type='{self.type}', status='{self.status}')"


class Setting(Base):
    """系统设置表"""
    __tablename__ = "settings"
    
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"Setting(key='{self.key}')"


class PushSubscription(Base):
    """Web Push 订阅表"""
    __tablename__ = "push_subscriptions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    p256dh: Mapped[str] = mapped_column(String(200), nullable=False)
    auth: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    def __repr__(self) -> str:
        return f"PushSubscription(id={self.id})"
