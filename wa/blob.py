import asyncio
import functools
import logging
from dataclasses import dataclass
from typing import IO

from types_boto3_s3.service_resource import Bucket

logger = logging.getLogger(__name__)


@dataclass
class Store:
    bucket: Bucket

    async def save(self, key: str, fin: IO[bytes] | str, mime: str):
        logger.info("save(%s): %s", key, mime)
        loop = asyncio.get_event_loop()

        if not isinstance(fin, str):
            await loop.run_in_executor(
                None,
                functools.partial(
                    self.bucket.upload_fileobj,
                    Fileobj=fin,
                    Key=key,
                    ExtraArgs={"ContentType": mime},
                ),
            )
            return

        obj = self.bucket.Object(key)
        await loop.run_in_executor(
            None,
            functools.partial(
                obj.put,
                Body=fin,
                ContentType=mime,
            ),
        )

    async def presigned(self, key: str, duration: int = 600):
        logger.info("presigned(%s): %s", key, duration)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(
                self.bucket.meta.client.generate_presigned_url,
                ClientMethod="get_object",
                Params={"Bucket": self.bucket.name, "Key": key},
                ExpiresIn=duration,
            ),
        )
