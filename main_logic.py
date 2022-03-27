import asyncio
import json
import random
import re
import sys
from typing import Optional, Dict

import loguru
import vkbottle.user

import utils

DEFAULT_SUBSTITUTIONS_FILE_NAME = "substitutions.json"
DEFAULT_ATTACHMENTS_FILE_NAME = "attachments.json"

HELP_MESSAGE = open("help_message.txt", encoding="utf-8").read()


class Bot:

    def __init__(
            self, bot: vkbottle.User,
            substitutions: Dict[str, str], substitutions_file_name: str,
            prefix: str, attachments: Dict[str, str],
            attachments_file_name: str, uline_and_cross_regex: re.Pattern):
        self.bot = bot
        # -----
        self.substitutions = substitutions
        self.substitutions_regex: Optional[re.Pattern] = None
        self.attachments_regex: Optional[re.Pattern] = None
        self.prefix = prefix
        self.attachments = attachments
        self.cache_substitutions_regex()
        self.cache_attachments()
        # -----
        self.uline_and_cross_regex = uline_and_cross_regex
        self.my_id: Optional[int] = None
        self.substitutions_file_name = substitutions_file_name
        self.attachments_file_name = attachments_file_name

    def cache_substitutions_regex(self) -> None:
        self.substitutions_regex = re.compile(self.prefix + "(" + "|".join(
            re.escape(key) for key in self.substitutions.keys()
        ) + ")")

    def cache_attachments(self) -> None:
        self.attachments_regex = re.compile(self.prefix + "(" + "|".join(
            re.escape(key) for key in self.attachments.keys()
        ) + ")")

    def cache_and_save_attachments(self) -> None:
        with open(self.attachments_file_name, "w", encoding="utf-8") as file:
            json.dump(self.attachments, file, indent=4)
        self.cache_attachments()

    @classmethod
    def make(cls, substitutions_prefix: str = "%"):
        bot = vkbottle.User(token=open("token.txt").read())
        obj = cls(
            bot=bot,
            substitutions=json.load(
                open(DEFAULT_SUBSTITUTIONS_FILE_NAME, encoding="utf-8")
            ),
            substitutions_file_name=DEFAULT_SUBSTITUTIONS_FILE_NAME,
            prefix=substitutions_prefix,
            attachments=json.load(
                open(DEFAULT_ATTACHMENTS_FILE_NAME, encoding="utf-8")
            ),
            attachments_file_name=DEFAULT_ATTACHMENTS_FILE_NAME,
            uline_and_cross_regex=re.compile(
                rf"{substitutions_prefix}(?P<method>uline|cross)"
                rf"(?P<text>.+?){substitutions_prefix}(\1)"
            )
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
        return self.substitutions[key.group(1)]

    # noinspection PyMethodMayBeStatic
    def _get_attachments(self, additional_attachments_list: list):
        def inner(key: re.Match):
            additional_attachments_list.append(self.attachments[key.group(1)])
            return ""
        return inner

    async def on_message(self, message: vkbottle.user.Message):
        if message.from_id == self.my_id and message.text:
            text = message.text
            if text == "///get-substitutions":
                await self._send_message(
                    original_message=message, text=json.dumps(
                        self.substitutions, indent=4, ensure_ascii=False,
                    )
                )
            elif text == "///help":
                await message.answer(HELP_MESSAGE)
            elif text.startswith("///set-attachments"):
                attachment_name = (
                    text[18:].lstrip()  # len("///add-attachments")
                )
                attachments_string = utils.get_attachments_string(message)
                if attachments_string:
                    self.attachments[attachment_name] = attachments_string
                    self.cache_and_save_attachments()
                    await message.answer("Attachments were set")
                else:
                    await message.answer("Attachments not found")
            elif text.startswith("///delete-attachments"):
                attachment_name = (
                    text[21:].lstrip()  # len("///delete-attachments")
                )
                try:
                    del self.attachments[attachment_name]
                except KeyError:
                    await message.answer("Attachments not found")
                else:
                    self.cache_and_save_attachments()
                    await message.answer("Attachments successfully deleted")
            elif text == "///get-attachments":
                await message.answer(json.dumps(
                    self.attachments, indent=4, ensure_ascii=False,
                ))
            elif text.startswith("///set-substitutions"):
                new_substitutions_string = (
                    text[20:].lstrip()  # len("///set-substitutions")
                )
                try:
                    self.substitutions = json.loads(new_substitutions_string)
                except json.JSONDecodeError:
                    await message.answer("Unable to decode JSON!")
                else:
                    self.cache_substitutions_regex()
                    json.dump(self.substitutions, open(
                        self.substitutions_file_name, "w", encoding="utf-8"
                    ), indent=4)
                    await message.answer("JSON was loaded successfully!")
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
                attachments = utils.get_attachments_string(message)
                try:
                    additional_attachments = []
                    new_string, changes_amount = self.attachments_regex.subn(
                        self._get_attachments(additional_attachments), text
                    )
                except KeyError:
                    pass
                else:
                    if changes_amount != 0:
                        text = new_string
                        text_was_updated = True
                        if attachments:
                            attachments += ","
                        attachments += ",".join(additional_attachments)
                new_string, changes_amount = self.uline_and_cross_regex.subn(
                    lambda match: utils.cross_uline_dict[match.group("method")](
                        match.group("text")
                    ), text
                )
                if changes_amount != 0:
                    text = new_string
                    text_was_updated = True
                if text_was_updated:
                    await self.bot.api.messages.edit(
                        peer_id=message.peer_id, message_id=message.id,
                        message=text, keep_forward_messages=True,
                        dont_parse_links=True,
                        attachment=attachments
                    )


async def main():
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, level="WARNING")
    print("Starting!")
    await Bot.make(substitutions_prefix="%").start()


asyncio.get_event_loop().run_until_complete(main())
