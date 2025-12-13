import asyncio

from django.core.management.base import BaseCommand

from telegram_app.bot_service import build_application, daily_sender_loop


class Command(BaseCommand):
    help = "Run TG Yuk Monitor Telegram bot (admin-only) and send daily reports."

    def add_arguments(self, parser):
        parser.add_argument('--daily-hour', type=int, default=0)
        parser.add_argument('--daily-minute', type=int, default=5)

    def handle(self, *args, **options):
        hour = options['daily_hour']
        minute = options['daily_minute']
        asyncio.run(self._main(hour=hour, minute=minute))

    async def _main(self, *, hour: int, minute: int):
        application = build_application()

        await application.initialize()
        await application.start()
        await application.updater.start_polling()

        # background daily loop
        asyncio.create_task(daily_sender_loop(application, hour=hour, minute=minute))

        self.stdout.write(self.style.SUCCESS('Bot started. Press CTRL+C to stop.'))

        try:
            # keep alive
            await asyncio.Event().wait()
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
