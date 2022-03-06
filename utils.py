import vkbottle.user


def get_attachments_string(message: vkbottle.user.Message):
    attachments_list = []
    for attachment in message.attachments:
        typename = attachment.type.value
        attachment = getattr(attachment, typename)
        attachments_list.append(
            f"{typename}{attachment.owner_id}"
            f"_{attachment.id}"
        )
    return ",".join(attachments_list)


def merge(text, character):
    return "".join(character + t for t in text) + character


cross_uline_dict = {
    "cross": lambda text: merge(text, "&#0822;"),
    "uline": lambda text: merge(text, "\u0332")
}
