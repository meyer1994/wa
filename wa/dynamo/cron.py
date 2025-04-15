import asyncio
import datetime as dt
import enum
import logging
from typing import Any, AsyncIterator, Self

from croniter import croniter
from pynamodb import attributes as attr
from pynamodb.models import MetaProtocol, Model

logger = logging.getLogger(__name__)


def _now() -> dt.datetime:
    """Utility function to get the current UTC time."""
    return dt.datetime.now(dt.UTC)


class CronJob(Model):
    class Meta(MetaProtocol):
        pass

    class Status(enum.StrEnum):
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"

    id = attr.UnicodeAttribute(hash_key=True)
    index = attr.NumberAttribute(range_key=True)
    cron = attr.UnicodeAttribute()
    next_run = attr.UTCDateTimeAttribute()
    last_run = attr.UTCDateTimeAttribute(null=True)
    status = attr.UnicodeAttribute(default=Status.PENDING)
    data = attr.MapAttribute[str, Any](default=dict)
    error = attr.MapAttribute[str, Any](default=dict)

    @classmethod
    async def new(
        cls,
        id: str,
        cron: str,
        data: dict[str, Any] | None = None,
    ) -> Self:
        """Create a new job."""
        logger.info("new(%s)", id)
        if data is None:
            data = {}

        # For simplicity, we'll just use next minute for this example
        next_run = _now() + dt.timedelta(minutes=1)

        job = cls(id=id, cron=cron, next_run=next_run, data=data)
        await job.asave()
        return job

    @classmethod
    async def fetch_pending(cls) -> AsyncIterator[Self]:
        """Fetch pending jobs."""
        logger.info("fetch_pending()")
        queue: asyncio.Queue[Self | None] = asyncio.Queue()

        filter = cls.status == cls.Status.PENDING
        filter &= cls.next_run <= _now()

        def _producer():
            for job in cls.scan(filter):
                queue.put_nowait(job)

        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(None, _producer)
        future.add_done_callback(lambda _: queue.put_nowait(None))

        while True:
            item = await queue.get()
            if item is None:
                break
            yield item

        await future

    async def mark_running(self):
        """Mark this job as running."""
        logger.info("mark_running(%s, %s)", self.id, self.index)
        logger.debug(f"{self.last_run=}")
        logger.debug(f"{self.next_run=}")
        self.status = self.Status.RUNNING
        await self.asave()

    async def mark_completed(self):
        """Mark this job as completed and calculate next run time."""
        logger.info("mark_completed(%s, %s)", self.id, self.index)
        logger.debug(f"{self.last_run=}")
        logger.debug(f"{self.next_run=}")
        self.last_run = self.next_run
        iter = croniter(self.cron, _now())
        self.next_run = iter.get_next(dt.datetime)
        self.status = self.Status.PENDING
        await self.asave()

    async def mark_failed(self, error: str | None = None) -> None:
        """Mark this job as failed."""
        logger.info("mark_failed(%s)", self.id)
        logger.debug(f"{self.last_run=}")
        logger.debug(f"{self.next_run=}")
        self.status = self.Status.FAILED
        if error:
            self.error["message"] = error
        await self.asave()

    async def asave(self):
        """Save the job."""
        logger.info("asave(%s)", self.id)
        logger.debug(f"{self.last_run=}")
        logger.debug(f"{self.next_run=}")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.save)

    async def adelete(self):
        """Delete the job."""
        logger.info("adelete(%s)", self.id)
        logger.debug(f"{self.last_run=}")
        logger.debug(f"{self.next_run=}")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.delete)

    @classmethod
    async def aget(cls, id: str, range: int | float | None = None) -> Self:
        """Get the job."""
        logger.info("aget(%s)", id)
        logger.debug(f"{range=}")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.get, id, range)
