import contextlib
import logging
import secrets
from dataclasses import dataclass, field

import httpx
from httpx import AsyncClient

import wa.config

logger = logging.getLogger(__name__)


OLD_NUM_LENGTH = 12
"""Old brazilian numbers used to have 12 digits, now they have 13"""


@dataclass
class WhatsApp:
    access_token: str
    sender_id: str
    base_url: str = "https://graph.facebook.com/v22.0"
    verify_token: str | None = None

    client: AsyncClient = field(init=False, repr=False)

    def __post_init__(self):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        self.client = AsyncClient(base_url=self.base_url, headers=headers)

    @staticmethod
    def as_dep(cfg: wa.config.DepConfig) -> "WhatsApp":
        return WhatsApp(
            access_token=cfg.WHATSAPP_ACCESS_TOKEN,
            sender_id=cfg.WHATSAPP_SENDER_ID,
            verify_token=cfg.WHATSAPP_VERIFY_TOKEN,
        )

    def _url(self, *args: str) -> str:
        return "/".join([self.base_url, self.sender_id, *args])

    def _num(self, num: str) -> str:
        if len(num) == OLD_NUM_LENGTH:
            return num[:4] + "9" + num[4:]
        return num

    def validate(self, token: str) -> bool:
        if self.verify_token is None:
            return False
        if not secrets.compare_digest(self.verify_token, token):
            return False
        return True

    @contextlib.asynccontextmanager
    async def conn(self):
        async with self.client:
            yield self

    async def send(self, to: str, message: str):
        response = await self.client.post(
            url=self._url("messages"),
            json={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": self._num(to),
                "type": "text",
                "text": {"preview_url": False, "body": message},
            },
        )

        logger.debug("%s", response)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.error("%s", response.json())
            raise

        return response.json()

    async def reply(self, to: str, id: str, message: str):
        response = await self.client.post(
            url=self._url("messages"),
            json={
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": self._num(to),
                "context": {"message_id": id},
                "type": "text",
                "text": {"preview_url": False, "body": message},
            },
        )

        logger.debug("%s", response)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            logger.error("%s", response.json())
            raise

        return response.json()

    async def media(self, from_: str, id: str):
        raise NotImplementedError
        # url = self._url(id)
        # response = await self.client.get(url)
        # logger.debug("%s", response)
        # logger.debug("%s", response.headers)
        # logger.debug("%s", response.json())
        # return response.json()
