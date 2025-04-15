import asyncio
import logging

from mangum import Mangum

import wa.app
from wa import logs
from wa.config import Config
from wa.dynamo import init
from wa.dynamo.cron import CronJob

logger = logging.getLogger(__name__)

# This is simply the file used to run the app in AWS
app = wa.app.create()
handler = Mangum(app)


async def _acron_handler() -> None:
    async def _run(job: CronJob) -> None:
        try:
            await job.mark_running()
            logger.info("Running job %s", job.id)
            logger.debug("Job data: %s", job.data)
            await job.mark_completed()
        except Exception as e:
            logger.exception(f"exception({job.id=})")
            await job.mark_failed(str(e))

    async with asyncio.TaskGroup() as tg:
        async for job in CronJob.fetch_pending():
            tg.create_task(_run(job))


def cron_handler(event, context) -> None:
    cfg = Config()  # type: ignore
    init(cfg)
    logger.info("Cron handler called")
    logger.debug("Event: %s", event)
    asyncio.run(_acron_handler())


if __name__ == "__main__":
    logs.init()
    cron_handler({}, {})
