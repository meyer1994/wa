from wa.config import Config

from .cron import CronJob
from .messages import Message, MessageDocument, MessageImage, MessageText
from .tools import Tool, ToolCron, ToolCronItem, ToolTodo, ToolTodoItem
from .whatsapp import WhatsAppItem, WhatsAppMessage, WhatsAppStatus

__all__ = [
    "CronJob",
    "Message",
    "MessageDocument",
    "MessageImage",
    "MessageText",
    "Tool",
    "ToolCron",
    "ToolCronItem",
    "ToolTodo",
    "ToolTodoItem",
    "WhatsAppItem",
    "WhatsAppMessage",
    "WhatsAppStatus",
]


def init(cfg: Config):
    Message.Meta.table_name = cfg.DYNAMO_DB_TABLE_MESSAGES
    WhatsAppItem.Meta.table_name = cfg.DYNAMO_DB_TABLE_EVENTS
    Tool.Meta.table_name = cfg.DYNAMO_DB_TABLE_TOOLS
    CronJob.Meta.table_name = cfg.DYNAMO_DB_TABLE_CRON

    if cfg.AWS_ENDPOINT_URL:
        Message.Meta.host = cfg.AWS_ENDPOINT_URL
        WhatsAppItem.Meta.host = cfg.AWS_ENDPOINT_URL
        Tool.Meta.host = cfg.AWS_ENDPOINT_URL
        CronJob.Meta.host = cfg.AWS_ENDPOINT_URL
