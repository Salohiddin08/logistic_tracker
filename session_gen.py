from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = 34259513
api_hash = "558c38cc422e57adf957c21e0062c5fa"

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\n✅ STRING SESSION:\n")
    print(client.session.save())

