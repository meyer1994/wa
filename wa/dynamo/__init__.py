from wa.config import Config

from .messages import Message, MessageDocument, MessageImage, MessageText
from .tools import Tool, ToolTodo
from .whatsapp import WhatsAppItem, WhatsAppMessage, WhatsAppStatus


def init(cfg: Config):
    Message.Meta.table_name = cfg.DYNAMO_DB_TABLE_MESSAGES
    WhatsAppItem.Meta.table_name = cfg.DYNAMO_DB_TABLE_EVENTS
    Tool.Meta.table_name = cfg.DYNAMO_DB_TABLE_TOOLS

    if cfg.AWS_ENDPOINT_URL:
        Message.Meta.host = cfg.AWS_ENDPOINT_URL
        WhatsAppItem.Meta.host = cfg.AWS_ENDPOINT_URL
        Tool.Meta.host = cfg.AWS_ENDPOINT_URL
