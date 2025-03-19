import asyncio
import logging
from typing import Annotated

from pydantic import AliasChoices, Field
from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliImplicitFlag,
    CliPositionalArg,
    SettingsConfigDict,
)

import wa.app
import wa.config


class Commands(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    to: Annotated[
        CliPositionalArg[str],
        Field(description="The phone number to send the message to"),
    ]

    message: Annotated[
        CliPositionalArg[str],
        Field(description="The message to send"),
    ]

    verbose: Annotated[
        CliImplicitFlag[bool],
        Field(
            False,
            validation_alias=AliasChoices("v", "verbose"),
            description="Verbose output",
        ),
    ]


if __name__ == "__main__":
    args = CliApp.run(Commands)
    cfg = wa.config.Config()  # type: ignore

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    async def run():
        client = wa.app.dwhatsapp(cfg)
        message = client.create_message(to=args.to, content=args.message)
        result = await (await message.send(sender="TEST"))
        print(result)
        print(message.data)

    asyncio.run(run())
