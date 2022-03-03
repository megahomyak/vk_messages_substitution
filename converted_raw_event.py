from dataclasses import dataclass


@dataclass
class ConvertedRawUserMessage:
    id: int
    from_id: int
    peer_id: int
    text: str
    attachments: str

    @classmethod
    def from_raw_user_message(cls, message_contents: list):
        additional_info = message_contents[7]
        attachments_list = []
        attachment_number = 1
        try:
            while True:
                attachments_list.append(
                    additional_info[f"attach{attachment_number}_type"]
                    + additional_info[f"attach{attachment_number}"]
                )
                attachment_number += 1
        except KeyError:
            pass
        return cls(
            from_id=int(additional_info["from"]),
            peer_id=message_contents[3],
            text=message_contents[6],
            attachments=",".join(attachments_list),
            id=message_contents[1]
        )
