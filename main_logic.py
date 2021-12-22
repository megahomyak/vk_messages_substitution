import asyncio
import sys
from typing import Optional

import loguru
import vkbottle.user

SUBSTITUTIONS = {
    "nometa": "nometa.xyz",
    "pydocs": "docs.python.org/3/tutorial/index.html"
}


bot = vkbottle.user.User(token=open("token.txt").read())

my_id: Optional[int] = None


@bot.on.message()
async def on_message(message: vkbottle.user.Message):
    if message.from_id == my_id:
        try:
            substitution = SUBSTITUTIONS[message.text]
        except KeyError:
            pass
        else:
            await bot.api.messages.edit(
                peer_id=message.peer_id, message_id=message.id,
                message=substitution, keep_forward_messages=True,
                dont_parse_links=True
            )
            return


async def main():
    loguru.logger.remove()
    loguru.logger.add(sys.stdout, level="WARNING")
    me = (await bot.api.users.get())[0]
    global my_id
    my_id = me.id
    print("Starting!")
    await bot.run_polling()


asyncio.get_event_loop().run_until_complete(main())
