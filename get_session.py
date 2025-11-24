from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = 34259513
api_hash = "558c38cc422e57adf957c21e0062c5fa"

with TelegramClient(StringSession(), api_id, api_hash) as client:
    client.connect()

    print("📸 Telegram'da Settings > Devices'ga kiring")
    print("💡 Link a device -> QR Scan tanlang")

    client.qr_login()

    input("✅ QR ni scan qilgach Enter bosing...")

    print("\n✅ SESSION STRING:\n")
    print(client.session.save())

