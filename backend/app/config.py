"""配置管理模块"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "Hot Monitor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/hot_monitor.db"
    
    # OpenRouter AI 配置
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "anthropic/claude-3.5-sonnet"  # 默认模型
    
    # 邮件通知配置
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    NOTIFICATION_EMAIL: str = ""  # 接收通知的邮箱
    
    # Web Push 配置
    VAPID_PUBLIC_KEY: str = ""
    VAPID_PRIVATE_KEY: str = ""
    VAPID_CLAIMS_EMAIL: str = ""
    
    # 爬虫配置
    CRAWL_INTERVAL_MINUTES: int = 5  # 关键词监控间隔
    HOTSPOT_INTERVAL_MINUTES: int = 30  # 热点发现间隔
    REQUEST_TIMEOUT: int = 30  # 请求超时时间(秒)
    
    # 代理配置（可选）
    HTTP_PROXY: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
