import config

from ..logging import LOGGER
from ..error_logger import ErrorLoggingClient

assistants = []
assistantids = []


class Userbot:
    def __init__(self):
        self.one = ErrorLoggingClient(
            name="ANJALIAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=True,
            error_logger_name="Assistant 1",
        )
        self.two = ErrorLoggingClient(
            name="ANJALIAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
            no_updates=True,
            error_logger_name="Assistant 2",
        )
        self.three = ErrorLoggingClient(
            name="ANJALIAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
            no_updates=True,
            error_logger_name="Assistant 3",
        )
        self.four = ErrorLoggingClient(
            name="ANJALIAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
            no_updates=True,
            error_logger_name="Assistant 4",
        )

    async def start(self):
        LOGGER(__name__).info(f"Starting Assistants...")
        
        # Assistant 1
        if config.STRING1:
            if not self.one.is_connected:
                await self.one.start()
            try:
                await self.one.join_chat("https://t.me/betabot_hub")
                await self.one.join_chat("https://t.me/betabot_support")
                await self.one.join_chat("https://t.me/sukoon_s")
            except:
                pass
            assistants.append(1)
            try:
                await self.one.send_message(config.LOGGER_ID, "Assistant 1 Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 1 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin!"
                )
                exit()
            self.one.id = self.one.me.id
            self.one.name = self.one.me.mention
            self.one.username = self.one.me.username
            assistantids.append(self.one.id)
            LOGGER(__name__).info(f"Assistant 1 Started as {self.one.name}")

        # Assistant 2
        if config.STRING2:
            if not self.two.is_connected:
                await self.two.start()
            try:
                await self.two.join_chat("https://t.me/betabot_hub")
                await self.two.join_chat("https://t.me/betabot_support")
                await self.two.join_chat("https://t.me/sukoon_s")
            except:
                pass
            assistants.append(2)
            try:
                await self.two.send_message(config.LOGGER_ID, "Assistant 2 Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 2 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin!"
                )
                exit()
            self.two.id = self.two.me.id
            self.two.name = self.two.me.mention
            self.two.username = self.two.me.username
            assistantids.append(self.two.id)
            LOGGER(__name__).info(f"Assistant 2 Started as {self.two.name}")

        # Assistant 3
        if config.STRING3:
            if not self.three.is_connected:
                await self.three.start()
            try:
                await self.three.join_chat("https://t.me/betabot_hub")
                await self.three.join_chat("https://t.me/betabot_support")
                await self.three.join_chat("https://t.me/sukoon_s")
            except:
                pass
            assistants.append(3)
            try:
                await self.three.send_message(config.LOGGER_ID, "Assistant 3 Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 3 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin!"
                )
                exit()
            self.three.id = self.three.me.id
            self.three.name = self.three.me.mention
            self.three.username = self.three.me.username
            assistantids.append(self.three.id)
            LOGGER(__name__).info(f"Assistant 3 Started as {self.three.name}")

        # Assistant 4
        if config.STRING4:
            if not self.four.is_connected:
                await self.four.start()
            try:
                await self.four.join_chat("https://t.me/betabot_hub")
                await self.four.join_chat("https://t.me/betabot_support")
                await self.four.join_chat("https://t.me/sukoon_s")
            except:
                pass
            assistants.append(4)
            try:
                await self.four.send_message(config.LOGGER_ID, "Assistant 4 Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 4 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin!"
                )
                exit()
            self.four.id = self.four.me.id
            self.four.name = self.four.me.mention
            self.four.username = self.four.me.username
            assistantids.append(self.four.id)
            LOGGER(__name__).info(f"Assistant 4 Started as {self.four.name}")


    async def stop(self):
        LOGGER(__name__).info(f"Stopping Assistants...")
        try:
            if config.STRING1:
                if self.one.is_connected:
                    await self.one.stop()
            if config.STRING2:
                if self.two.is_connected:
                    await self.two.stop()
            if config.STRING3:
                if self.three.is_connected:
                    await self.three.stop()
            if config.STRING4:
                if self.four.is_connected:
                    await self.four.stop()
        except:
            pass
