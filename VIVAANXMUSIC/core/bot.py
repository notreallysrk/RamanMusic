import asyncio
import sys

from pyrogram import Client, errors
from pyrogram.enums import ChatMemberStatus

import config
from ..logging import LOGGER


class JARVIS(Client):
    START_ATTEMPTS = 4
    START_RETRY_DELAY = 10

    def __init__(self):
        super().__init__(
            name="VivaanXMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            workers=48,
            max_concurrent_transmissions=7,
        )
        LOGGER(__name__).info("Bot client initialized.")

    async def start(self):
        # Telegram's ImportBotAuthorization may time out during a temporary
        # Telegram/DC or hosting-network issue. Retry the main bot login cleanly.
        for attempt in range(1, self.START_ATTEMPTS + 1):
            try:
                await super().start()
                break
            except (TimeoutError, asyncio.TimeoutError, OSError, ConnectionError) as exc:
                LOGGER(__name__).warning(
                    "Main bot authorization connection failed "
                    f"(attempt {attempt}/{self.START_ATTEMPTS}): "
                    f"{type(exc).__name__}"
                )

                # A failed authorization can leave the MTProto connection open.
                # Disconnect it before attempting Client.start() again.
                try:
                    if getattr(self, "is_connected", False):
                        await self.disconnect()
                except Exception:
                    pass

                if attempt >= self.START_ATTEMPTS:
                    LOGGER(__name__).error(
                        "Main bot could not authenticate with Telegram after "
                        f"{self.START_ATTEMPTS} attempts. Check Heroku network "
                        "connectivity and verify BOT_TOKEN, API_ID and API_HASH."
                    )
                    raise

                await asyncio.sleep(self.START_RETRY_DELAY * attempt)

        me = await self.get_me()
        self.username, self.id = me.username, me.id
        self.name = f"{me.first_name} {me.last_name or ''}".strip()
        self.mention = me.mention

        try:
            await self.send_message(
                config.LOGGER_ID,
                (
                    f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b></u>\n\n"
                    f"ɪᴅ : <code>{self.id}</code>\n"
                    f"ɴᴀᴍᴇ : {self.name}\n"
                    f"ᴜsᴇʀɴᴀᴍᴇ : @{self.username}"
                ),
            )
        except (errors.ChannelInvalid, errors.PeerIdInvalid):
            LOGGER(__name__).error(
                "❌ Bot cannot access the log group/channel – add & promote it first!"
            )
            sys.exit()
        except Exception as exc:
            LOGGER(__name__).error(
                "❌ Bot has failed to access the log group. "
                f"Reason: {type(exc).__name__}"
            )
            sys.exit()

        try:
            member = await self.get_chat_member(config.LOGGER_ID, self.id)
            if member.status != ChatMemberStatus.ADMINISTRATOR:
                LOGGER(__name__).error(
                    "❌ Promote the bot as admin in the log group/channel."
                )
                sys.exit()
        except Exception as exc:
            LOGGER(__name__).error(
                f"❌ Could not check admin status: {type(exc).__name__}"
            )
            sys.exit()

        LOGGER(__name__).info(
            f"✅ Music Bot started as {self.name} (@{self.username})"
        )
