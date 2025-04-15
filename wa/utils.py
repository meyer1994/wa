import asyncio
import logging
from typing import Any, Callable, Coroutine

from wa.dynamo.cron import CronJob

logger = logging.getLogger(__name__)


class CronExecutor:
    def __init__(self, handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]]):
        self.handler = handler

    async def run(self) -> None:
        """Simple loop that checks for jobs every minute."""
        while True:
            try:
                # Process all pending jobs
                async for job in CronJob.fetch_pending():
                    try:
                        await job.mark_running()
                        await self.handler(job.data.as_dict())
                        await job.mark_completed()
                    except Exception as e:
                        logger.error(f"Error processing job {job.id}: {e}")
                        await job.mark_failed(str(e))

            except Exception as e:
                logger.error(f"Error in cron executor: {e}")

            # Sleep for 60 seconds before next check
            logger.info("Sleeping for 1 second")
            await asyncio.sleep(1)


async def handle_job(data: dict[str, Any]) -> None:
    print(f"Processing job with data: {data}")


async def main():
    executor = CronExecutor(handle_job)
    await executor.run()


if __name__ == "__main__":
    from wa.config import Config

    logging.basicConfig(level=logging.INFO)

    cfg = Config()  # type: ignore
    CronJob.Meta.table_name = cfg.DYNAMO_DB_TABLE_CRON
    if cfg.AWS_ENDPOINT_URL:
        CronJob.Meta.host = cfg.AWS_ENDPOINT_URL
    asyncio.run(main())
