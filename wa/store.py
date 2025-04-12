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

    async def save(self, key: str, fin: IO[bytes], mime: str):
        logger.info("save(%s)", key)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(
                self.bucket.upload_fileobj,
                Fileobj=fin,
                Key=key,
                ExtraArgs={"ContentType": mime},
            ),
        )

    async def load(self, key: str, fout: IO[bytes]):
        logger.info("load(%s)", key)
        loop = asyncio.get_event_loop()
        obj = self.bucket.Object(key)
        func = functools.partial(obj.download_fileobj, fout)
        return await loop.run_in_executor(None, func)
