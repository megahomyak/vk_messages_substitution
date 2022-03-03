import asyncio
import json
import random
import re
import sys
from typing import Optional, Dict

import loguru
import vkbottle.user

DEFAULT_SUBSTITUTIONS_FILE_NAME = "substitutions.json"

ULINE_AND_CROSS_REGEX = re.compile(
    r"%(?P<method>uline|cross)(?P<text>.+)%(\1)"
)


def merge(text, character):
    return "".join(character + t for t in text) + character


cross_uline_dict = {
    "cross": lambda text: merge(text, "&#0822;"),
    "uline": lambda text: merge(text, "\u0332")
}


class Bot:

    def __init__(
            self, bot: vkbottle.User, substitutions_string: str,
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
        self.substitutions_regex = re.compile(self.prefix + "(" + "|".join(
            self.substitutions.keys()
        ) + ")")

    @classmethod
    def make(cls, substitutions_prefix: str = "%"):
        bot = vkbottle.User(token=open("token.txt").read())
        substitutions_string = (
            open(DEFAULT_SUBSTITUTIONS_FILE_NAME, encoding="utf-8").read()
        )
        obj = cls(
            bot=bot,
            substitutions_string=substitutions_string,
            substitutions=json.loads(substitutions_string),
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
        text = key.group(1)
        if text in ("cross", "uline"):
            return text
        return self.substitutions[key.group(1)]

    async def on_message(self, message: vkbottle.user.Message):
        if message.from_id == self.my_id:
            text = message.text
            if text == "///get-substitutions":
                await self._send_message(
                    original_message=message, text=self.substitutions_string
                )
            elif text.startswith("///set-substitutions"):
                new_substitutions_string = (
                    text[20:].lstrip()  # len("///set-substitutions")
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
                text_was_updated = False
                try:
                    new_string, changes_amount = self.substitutions_regex.subn(
                        self._get_substitution, text
                    )
                except KeyError:
                    pass
                else:
                    if changes_amount != 0:
                        text = new_string
                        text_was_updated = True
                new_string, changes_amount = ULINE_AND_CROSS_REGEX.subn(
                    lambda match: cross_uline_dict[match.group("method")](
                        match.group("text")
                    ), text
                )
                if changes_amount != 0:
                    text = new_string
                    text_was_updated = True
                if text_was_updated:
                    attachments_list = []
                    for attachment in message.attachments:
                        typename = attachment.type.value
                        attachment = getattr(attachment, typename)
                        attachments_list.append(
                            f"{typename}{attachment.owner_id}"
                            f"_{attachment.id}"
                        )
                    await self.bot.api.messages.edit(
                        peer_id=message.peer_id, message_id=message.id,
                        message=text, keep_forward_messages=True,
                        dont_parse_links=True,
                        attachment=",".join(attachments_list)
                    )


async def main():
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, level="WARNING")
    print("Starting!")
    await Bot.make(substitutions_prefix="%").start()


asyncio.get_event_loop().run_until_complete(main())
