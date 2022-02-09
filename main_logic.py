import asyncio
import json
import random
import re
import sys
from typing import Optional, Dict

import loguru
import vkbottle.user

DEFAULT_SUBSTITUTIONS_FILE_NAME = "substitutions.json"


class Bot:

    def __init__(
            self, bot: vkbottle.user.User, substitutions_string: str,
            substitutions: Dict[str, str], substitutions_file_name: str,
            prefix: str):
        self.bot = bot
        self.substitutions_string = substitutions_string
        self.substitutions = substitutions
        self.substitutions_regex: Optional[re.Pattern] = None
        self.prefix = prefix
        self.cache_substitutions_regex()
        self.my_id: Optional[int] = None
        self.substitutions_file_name = substitutions_file_name

    def cache_substitutions_regex(self) -> None:
        self.substitutions_regex = re.compile("|".join(
            self.prefix + substitution for substitution in self.substitutions
        ))

    @classmethod
    def make(cls, substitutions_prefix: str = "%"):
        bot = vkbottle.user.User(token=open("token.txt").read())
        substitutions_string = (
            open(DEFAULT_SUBSTITUTIONS_FILE_NAME, encoding="utf-8").read()
        )
        obj = cls(
            bot=bot,
            substitutions_string=substitutions_string,
            substitutions=json.loads(substitutions_string).items(),
            substitutions_file_name=DEFAULT_SUBSTITUTIONS_FILE_NAME,
            prefix=substitutions_prefix
        )
        bot.on.message()(obj.on_message)
        return obj

    async def start(self):
        me = (await self.bot.api.users.get())[0]
        self.my_id = me.id
        await self.bot.run_polling()

    async def _send_message(
            self, original_message: vkbottle.user.Message, text: str):
        await self.bot.api.messages.send(
            peer_id=original_message.peer_id, message=text,
            dont_parse_links=True, disable_mentions=True,
            random_id=random.randint(-1_000_000, 1_000_000)
        )

    def _get_substitution(self, key: re.Match):
        return self.substitutions[key.group(0)]

    async def on_message(self, message: vkbottle.user.Message):
        if message.from_id == self.my_id:
            if message.text == "///get-substitutions":
                await self._send_message(
                    original_message=message, text=self.substitutions_string
                )
            elif message.text.startswith("///set-substitutions"):
                new_substitutions_string = (
                    message.text[20:].lstrip()  # len("///set-substitutions")
                )
                try:
                    self.substitutions = json.loads(new_substitutions_string)
                except json.JSONDecodeError:
                    await self._send_message(
                        original_message=message, text="Unable to decode JSON!"
                    )
                else:
                    self.cache_substitutions_regex()
                    open(
                        self.substitutions_file_name, "w", encoding="utf-8"
                    ).write(new_substitutions_string)
                    self.substitutions_string = new_substitutions_string
                    await self._send_message(
                        original_message=message,
                        text="JSON was loaded successfully!"
                    )
            else:
                try:
                    new_string, changes_amount = self.substitutions_regex.subn(
                        self._get_substitution, message.text
                    )
                except KeyError:
                    pass
                else:
                    if changes_amount != 0:
                        await self.bot.api.messages.edit(
                            peer_id=message.peer_id, message_id=message.id,
                            message=new_string, keep_forward_messages=True,
                            dont_parse_links=True
                        )
                        return


async def main():
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, level="WARNING")
    print("Starting!")
    await Bot.make(substitutions_prefix="%").start()


asyncio.get_event_loop().run_until_complete(main())
