# VK_MESSAGES_SUBSTITUTION

> WARNING: "substitutions" are just text substitutions, while "attachments" are being added to the current message as attachments

Also don't forget to put your token in `token.txt`, you know...

`attachments.json` **SHOULD NOT BE FILLED MANUALLY!**
`substitutions.json` **SHOULD BE FILLED MANUALLY!** (format: `{"pattern": "substitution", "pattern": "substitution", ...}`)

`uline` and `cross` do not depend on any of the configs.
If you surround some text with the `uline` macro, the text surrounded will be underlined,
if you surround some text with the `cross` macro, the text surrounded will be crossed out.

Default macro prefix is `%`

# Commands

* `///set-substitutions {json}`
* `///get-substitutions`

* `///set-attachments {name}` - set attachments from the current message to a specified key
* `///delete-attachments {name}` - delete attachments by the specified name
* `///get-attachments` - get attachments JSON, pretty useless

* `///help` - this message
