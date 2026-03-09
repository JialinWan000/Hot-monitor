"""Pydantic 数据模型 - 用于API请求和响应验证

定义所有API接口的请求和响应数据结构，包含完整的字段说明和验证规则。
这些模型会自动生成Swagger文档中的Schema定义。
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict, EmailStr


# ==================== 关键词相关 ====================

class KeywordBase(BaseModel):
    """关键词基础模型"""
    keyword: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="要监控的关键词内容，如 'GPT-5'、'Claude 4'",
        json_schema_extra={"example": "GPT-5"}
    )
    category: Optional[str] = Field(
        None, 
        max_length=50, 
        description="关键词分类，用于组织管理，如 'AI'、'编程'、'科技'",
        json_schema_extra={"example": "AI"}
    )
    priority: Optional[str] = Field(
        "normal",
        description="优先级：low(低)、normal(普通)、high(高)、critical(紧急)",
        json_schema_extra={"example": "high"}
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="关键词的详细描述说明",
        json_schema_extra={"example": "监控OpenAI最新大模型发布动态"}
    )


class KeywordCreate(KeywordBase):
    """创建关键词请求
    
    用于添加新的监控关键词，系统会自动对关键词进行去重检查。
    """
    is_active: bool = Field(
        True,
        description="是否立即启用监控，默认为true"
    )


class KeywordUpdate(BaseModel):
    """更新关键词请求
    
    支持部分更新，只需传入要修改的字段。
    """
    keyword: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100,
        description="关键词内容"
    )
    category: Optional[str] = Field(
        None, 
        max_length=50,
        description="分类标签"
    )
    priority: Optional[str] = Field(
        None,
        description="优先级：low/normal/high/critical"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="详细描述"
    )
    is_active: Optional[bool] = Field(
        None,
        description="是否启用监控"
    )


class KeywordResponse(KeywordBase):
    """关键词响应模型
    
    返回完整的关键词信息，包括ID、时间戳等系统字段。
    """
    id: int = Field(..., description="关键词唯一标识ID")
    is_active: bool = Field(..., description="是否启用监控")
    match_count: int = Field(0, description="匹配到的热点数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="最后更新时间")
    
    model_config = ConfigDict(from_attributes=True)


# ==================== 热点相关 ====================

class HotspotBase(BaseModel):
    """热点基础模型"""
    title: str = Field(
        ..., 
        max_length=500, 
        description="热点标题",
        json_schema_extra={"example": "OpenAI发布GPT-5，性能提升10倍"}
    )
    content: Optional[str] = Field(
        None, 
        description="热点正文内容",
        json_schema_extra={"example": "今日，OpenAI正式发布了..."}
    )
    source: str = Field(
        ..., 
        max_length=50, 
        description="来源平台标识：twitter/bing/google/duckduckgo/hackernews/github/zhihu/reddit",
        json_schema_extra={"example": "hackernews"}
    )
    source_url: Optional[str] = Field(
        None, 
        max_length=2000, 
        description="原文链接URL",
        json_schema_extra={"example": "https://news.ycombinator.com/item?id=123456"}
    )


class HotspotCreate(HotspotBase):
    """创建热点请求（内部使用）"""
    pass


class HotspotResponse(HotspotBase):
    """热点响应模型
    
    返回完整的热点信息，包括AI分析结果。
    """
    id: int = Field(..., description="热点唯一标识ID")
    summary: Optional[str] = Field(None, description="AI生成的内容摘要（50字以内）")
    score: Optional[float] = Field(None, ge=0, le=100, description="AI重要性评分（0-100），>=70为高分热点")
    is_verified: bool = Field(False, description="AI是否已完成验证分析")
    is_fake: bool = Field(False, description="AI判断是否可能为虚假信息")
    ai_analysis: Optional[str] = Field(None, description="AI详细分析内容（100字以内）")
    tags: Optional[List[str]] = Field(None, description="AI生成的标签列表", json_schema_extra={"example": ["AI", "GPT", "OpenAI"]})
    notified: bool = Field(False, description="是否已发送通知")
    read: bool = Field(False, description="是否已读")
    published_at: Optional[datetime] = Field(None, description="原始发布时间")
    discovered_at: datetime = Field(..., description="系统发现时间")
    keywords: List[KeywordResponse] = Field(default=[], description="关联的关键词列表")
    
    model_config = ConfigDict(from_attributes=True)


class HotspotListResponse(BaseModel):
    """热点列表分页响应"""
    items: List[HotspotResponse] = Field(..., description="热点列表")
    total: int = Field(..., description="符合条件的总数量")
    page: int = Field(..., description="当前页码（从1开始）")
    page_size: int = Field(..., description="每页数量")


class HotspotSearchRequest(BaseModel):
    """热点搜索请求
    
    用于搜索特定领域的热点，不依赖已配置的关键词。
    """
    domain: str = Field(
        ..., 
        description="搜索领域/主题，如 'AI大模型'、'区块链'",
        json_schema_extra={"example": "AI大模型"}
    )
    sources: Optional[List[str]] = Field(
        None, 
        description="指定数据源列表，不指定则搜索所有数据源",
        json_schema_extra={"example": ["hackernews", "github", "reddit"]}
    )


# ==================== 通知相关 ====================

class NotificationResponse(BaseModel):
    """通知记录响应"""
    id: int = Field(..., description="通知记录ID")
    hotspot_id: int = Field(..., description="关联的热点ID")
    type: str = Field(..., description="通知类型：push(浏览器推送) / email(邮件)")
    status: str = Field(..., description="发送状态：pending(等待) / sent(已发送) / failed(失败)")
    error_message: Optional[str] = Field(None, description="失败时的错误信息")
    created_at: datetime = Field(..., description="创建时间")
    sent_at: Optional[datetime] = Field(None, description="发送时间")
    
    model_config = ConfigDict(from_attributes=True)


class PushSubscriptionCreate(BaseModel):
    """Web Push 订阅请求
    
    前端获取浏览器推送订阅信息后，调用此接口保存到服务端。
    """
    endpoint: str = Field(
        ..., 
        description="推送服务端点URL，由浏览器PushManager生成",
        json_schema_extra={"example": "https://fcm.googleapis.com/fcm/send/xxx..."}
    )
    keys: dict = Field(
        ..., 
        description="加密密钥对象，必须包含 p256dh 和 auth 两个字段",
        json_schema_extra={"example": {"p256dh": "BNcRdreALRFX...", "auth": "tBHItJI5sv..."}}
    )


class NotificationSettingsUpdate(BaseModel):
    """通知设置更新请求
    
    支持部分更新，只需传入要修改的字段。
    """
    email_enabled: Optional[bool] = Field(
        None,
        description="是否启用邮件通知"
    )
    push_enabled: Optional[bool] = Field(
        None,
        description="是否启用浏览器推送通知"
    )
    notification_email: Optional[str] = Field(
        None,
        description="接收通知的邮箱地址",
        json_schema_extra={"example": "user@example.com"}
    )


class NotificationSettingsResponse(BaseModel):
    """通知设置响应"""
    email_enabled: bool = Field(False, description="邮件通知是否启用")
    push_enabled: bool = Field(False, description="浏览器推送是否启用")
    notification_email: Optional[str] = Field(None, description="通知邮箱地址")


# ==================== 系统设置 ====================

class SettingUpdate(BaseModel):
    """系统设置更新请求"""
    key: str = Field(
        ...,
        description="设置项的键名，如 'crawl_interval'、'ai_model'",
        json_schema_extra={"example": "crawl_interval"}
    )
    value: str = Field(
        ...,
        description="设置项的值，始终为字符串类型",
        json_schema_extra={"example": "10"}
    )


class SettingResponse(BaseModel):
    """系统设置响应"""
    key: str = Field(..., description="设置项键名")
    value: str = Field(..., description="设置项值")
    description: Optional[str] = Field(None, description="设置项说明")
    updated_at: datetime = Field(..., description="最后更新时间")
    
    model_config = ConfigDict(from_attributes=True)


# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    """通用消息响应
    
    用于返回操作结果消息。
    """
    message: str = Field(..., description="响应消息内容")
    success: bool = Field(True, description="操作是否成功")


class ErrorResponse(BaseModel):
    """错误响应
    
    用于返回错误信息。
    """
    message: str = Field(..., description="错误消息")
    detail: Optional[Any] = Field(None, description="详细错误信息")
    success: bool = Field(False, description="始终为false")


# ==================== 统计数据 ====================

class DashboardStats(BaseModel):
    """仪表盘统计数据
    
    提供系统各项指标的统计数据，用于仪表盘展示。
    """
    total_keywords: int = Field(0, description="总关键词数量")
    active_keywords: int = Field(0, description="已启用的关键词数量")
    total_hotspots: int = Field(0, description="总热点数量")
    unread_hotspots: int = Field(0, description="未读热点数量")
    today_hotspots: int = Field(0, description="今日发现的热点数量")
    notifications_sent: int = Field(0, description="已成功发送的通知数量")
