import asyncio
import logging

from mangum import Mangum

import wa.app
import wa.deps as deps
from wa import logs
from wa.config import Config
from wa.dynamo import init
from wa.dynamo.cron import CronJob
from wa.whats.client import WhatsApp

logger = logging.getLogger(__name__)

# This is simply the file used to run the app in AWS
app = wa.app.create()
handler = Mangum(app)


async def _acron_handler(client: WhatsApp) -> None:
    async def _run(job: CronJob) -> None:
        try:
            await job.mark_running()
            logger.info(f"_run({job.id=})")
            logger.debug(f"{job.data=}")

            content = "\n".join(
                [
                    "_Executed from cron:_",
                    job.data["content"],
                ]
            )

            await client.send(job.data["to"], content)
            await job.adelete()  # this makes every job be a one-off job :)
        except Exception:
            logger.exception(f"exception({job.id=})")
            try:
                await job.adelete()  # just delete it
                # await job.mark_failed(str(e))
            except Exception:
                logger.exception(f"exception({job.id=})")
                raise
            raise

    async with asyncio.TaskGroup() as tg:
        async for job in CronJob.fetch_pending():
            tg.create_task(_run(job))


def cron_handler(event, context) -> None:
    cfg = Config()  # type: ignore
    init(cfg)
    logs.init()
    client = deps.dep_whatsapp(cfg)
    logger.info("Cron handler called")
    logger.debug("Event: %s", event)
    asyncio.run(_acron_handler(client))


if __name__ == "__main__":
    logs.init()
    cron_handler({}, {})
