import datetime as dt
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, Tag, TypeAdapter


class Metadata(BaseModel):
    display_phone_number: str
    phone_number_id: str


class ProfileObject(BaseModel):
    name: str


class ContactObject(BaseModel):
    wa_id: str
    profile: ProfileObject
    user_id: str | None = None


class ErrorDataObject(BaseModel):
    details: str


class ErrorObject(BaseModel):
    code: int
    title: str
    message: str | None = None
    error_data: ErrorDataObject | None = None


class TextObject(BaseModel):
    body: str


class ButtonObject(BaseModel):
    payload: str
    text: str


class AudioObject(BaseModel):
    id: str
    mime_type: str


class DocumentObject(BaseModel):
    caption: str | None = None
    filename: str
    sha256: str | None = None
    id: str
    mime_type: str


class ImageObject(BaseModel):
    caption: str | None = None
    sha256: str | None = None
    id: str
    mime_type: str


class VideoObject(BaseModel):
    caption: str | None = None
    sha256: str | None = None
    id: str
    mime_type: str


class StickerObject(BaseModel):
    id: str
    mime_type: str
    sha256: str | None = None
    animated: bool | None = None


class ContextObject(BaseModel):
    forwarded: bool | None = None
    frequently_forwarded: bool | None = None
    from_: str | None = None
    id: str | None = None
    referred_product: dict[str, Any] | None = None


class ReferralObject(BaseModel):
    source_url: str
    source_id: str
    source_type: str
    headline: str | None = None
    body: str | None = None
    media_type: str | None = None
    image_url: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None


class LocationObject(BaseModel):
    latitude: float
    longitude: float
    name: str | None = None
    address: str | None = None


class SystemObject(BaseModel):
    body: str
    identity: str
    type: Literal["customer_changed_number", "customer_identity_changed"]
    wa_id: str | None = None
    customer: dict[str, Any] | None = None


class InteractiveReplyButtonObject(BaseModel):
    id: str
    title: str


class InteractiveReplyObject(BaseModel):
    id: str
    title: str
    description: str | None = None


class InteractiveListReplyObject(BaseModel):
    id: str
    title: str
    description: str | None = None


class InteractiveObject(BaseModel):
    type: Literal["button_reply", "list_reply"]
    button_reply: InteractiveReplyButtonObject | None = None
    list_reply: InteractiveListReplyObject | None = None


class OrderProductItemObject(BaseModel):
    product_retailer_id: str
    quantity: str
    item_price: str
    currency: str


class OrderObject(BaseModel):
    catalog_id: str
    text: str | None = None
    product_items: list[OrderProductItemObject]


class MessageBase(BaseModel):
    from_: Annotated[str, Field(alias="from")]
    id: str
    timestamp: dt.datetime
    context: ContextObject | None = None
    errors: list[ErrorObject] = []
    referral: ReferralObject | None = None


class TextMessage(MessageBase):
    type: Literal["text"] = "text"
    text: TextObject


class ButtonMessage(MessageBase):
    type: Literal["button"] = "button"
    button: ButtonObject


class AudioMessage(MessageBase):
    type: Literal["audio"] = "audio"
    audio: AudioObject


class DocumentMessage(MessageBase):
    type: Literal["document"] = "document"
    document: DocumentObject


class ImageMessage(MessageBase):
    type: Literal["image"] = "image"
    image: ImageObject


class VideoMessage(MessageBase):
    type: Literal["video"] = "video"
    video: VideoObject


class StickerMessage(MessageBase):
    type: Literal["sticker"] = "sticker"
    sticker: StickerObject


class InteractiveMessage(MessageBase):
    type: Literal["interactive"] = "interactive"
    interactive: InteractiveObject


class OrderMessage(MessageBase):
    type: Literal["order"] = "order"
    order: OrderObject


class SystemMessage(MessageBase):
    type: Literal["system"] = "system"
    system: SystemObject


class LocationMessage(MessageBase):
    type: Literal["location"] = "location"
    location: LocationObject


class UnknownMessage(MessageBase):
    type: Literal["unknown"] = "unknown"


MessageObject = Annotated[
    Union[
        TextMessage,
        ButtonMessage,
        AudioMessage,
        DocumentMessage,
        ImageMessage,
        VideoMessage,
        StickerMessage,
        InteractiveMessage,
        OrderMessage,
        SystemMessage,
        LocationMessage,
        UnknownMessage,
    ],
    Tag("type"),
]

MessageObjectAdapter: TypeAdapter[MessageObject] = TypeAdapter(MessageObject)


class OriginObject(BaseModel):
    type: Literal[
        "authentication",
        "marketing",
        "utility",
        "service",
        "referral_conversion",
    ]


class ConversationObject(BaseModel):
    id: str
    origin: OriginObject | None = None
    expiration_timestamp: str | None = None


class PricingObject(BaseModel):
    category: Literal[
        "authentication",
        "authentication-international",
        "marketing",
        "utility",
        "service",
        "referral_conversion",
    ]
    pricing_model: str


class StatusObject(BaseModel):
    id: str
    recipient_id: str
    status: Literal["delivered", "read", "sent"]
    timestamp: dt.datetime
    conversation: ConversationObject | None = None
    pricing: PricingObject | None = None
    errors: list[ErrorObject] | None = None
    biz_opaque_callback_data: str | None = None


class Value(BaseModel):
    messaging_product: Literal["whatsapp"]
    metadata: Metadata

    statuses: list[StatusObject] = []
    messages: list[MessageObject] = []
    contacts: list[ContactObject] = []
    errors: list[ErrorObject] = []


class Change(BaseModel):
    value: Value
    field: Literal["messages"]


class Entry(BaseModel):
    id: Annotated[str, Field(pattern=r"^\d+$")]
    changes: list[Change]


class Webhook(BaseModel):
    object: Literal["whatsapp_business_account"]
    entry: list[Entry]

    def messages(self) -> list[MessageObject]:
        messages = []
        for entry in self.entry:
            for change in entry.changes:
                messages.extend(change.value.messages)
        return messages

    def statuses(self) -> list[StatusObject]:
        statuses = []
        for entry in self.entry:
            for change in entry.changes:
                statuses.extend(change.value.statuses)
        return statuses
