from telethon import TelegramClient, Button
from telethon.sessions import StringSession
import asyncio
from datetime import datetime
import logging
import random
from config import *

# تنظیمات لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ProxyCollector:
    def __init__(self):
        # ایجاد کلاینت تلگرام
        self.client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        self.proxies = []

    async def initialize(self):
        # راه‌اندازی کلاینت
        await self.client.start()
        logger.info("کلاینت راه‌اندازی شد")
        # دریافت موجودیت کانال مقصد
        self.dest_channel = await self.client.get_entity(DESTINATION_CHANNEL)

    async def collect_proxies(self):
        # پاکسازی لیست پروکسی‌ها
        self.proxies.clear()
        
        # جمع‌آوری پروکسی‌ها از کانال‌های منبع
        for channel in SOURCE_CHANNELS:
            try:
                channel_entity = await self.client.get_entity(channel)
                messages = await self.client.get_messages(channel_entity, limit=20)
                
                for msg in messages:
                    if not msg.reply_markup:
                        continue
                        
                    for row in msg.reply_markup.rows:
                        for button in row.buttons:
                            if hasattr(button, 'url'):
                                url = button.url
                                # پاکسازی URL از کاراکترهای غیرمجاز
                                if ('t.me/proxy?' in url or 'tg://proxy?' in url) and 'server=' in url:
                                    # حذف پارامترهای اضافی (مثل @Glype)
                                    url = url.split('&@')[0]  # حذف هر چیزی بعد از &@
                                    # جایگزینی آدرس‌های نادرست
                                    url = url.replace('https://t.me/', 'tg://').replace('http://t.me/', 'tg://')
                                    # حذف فضاهای خالی
                                    url = url.strip()
                                    # اعتبارسنجی نهایی
                                    if self.validate_proxy_url(url):
                                        self.proxies.append(url)

            except Exception as e:
                logger.error(f"خطا در کانال {channel}: {str(e)}")
                continue

        # حذف پروکسی‌های تکراری
        self.proxies = list(dict.fromkeys(self.proxies))
        logger.info(f"تعداد پروکسی‌های یکتا: {len(self.proxies)}")

    def validate_proxy_url(self, url):
        # بررسی فرمت صحیح URL پروکسی
        if not url.startswith('tg://proxy?'):
            return False
        params = ['server=', 'port=', 'secret=']
        return all(param in url for param in params)

    def select_proxies(self):
        # انتخاب تصادفی پروکسی‌ها
        if not self.proxies:
            return []
        count = min(PROXIES_PER_MESSAGE, len(self.proxies))
        return random.sample(self.proxies, count)

    async def send_proxy_message(self):
        try:
            await self.collect_proxies()
            
            if not self.proxies:
                logger.warning("پروکسی یافت نشد")
                return

            selected = self.select_proxies()
            if not selected:
                return

            # ساخت دکمه‌ها
            buttons = []
            # دکمه‌های پروکسی
            for proxy in selected:
                # اعتبارسنجی نهایی قبل از افزودن به دکمه
                if self.validate_proxy_url(proxy):
                    buttons.append([Button.url("🔐 MTProto Proxy", url=proxy)])
                else:
                    logger.warning(f"پروکسی نامعتبر حذف شد: {proxy}")

            # دکمه عضویت در کانال
            buttons.append([Button.url("📢 عضویت در کانال", url=f"t.me/{self.dest_channel.username}")])

            # ساخت متن پیام
            message_text = (
                "🔰 پروکسی‌های تلگرام\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "📌 برای اتصال روی دکمه‌های زیر کلیک کنید\n\n"
                f"🔄 تعداد پروکسی‌ها: {len(buttons)-1}"  # منهای دکمه عضویت
            )

            # ارسال پیام با دکمه‌ها
            await self.client.send_message(
                self.dest_channel,
                message_text,
                buttons=buttons,
                link_preview=False
            )

            logger.info(f"پیام با {len(buttons)-1} پروکسی معتبر ارسال شد")
        except Exception as e:
            logger.error(f"خطا در ارسال پیام: {str(e)}")

    async def run(self):
        # اجرای اصلی برنامه
        while True:
            try:
                await self.send_proxy_message()
                logger.info(f"انتظار برای {INTERVAL_MINUTES} دقیقه...")
                await asyncio.sleep(INTERVAL_MINUTES * 60)
            except Exception as e:
                logger.error(f"خطا در اجرا: {str(e)}")
                await asyncio.sleep(60)

async def main():
    # ایجاد نمونه‌ای از کلاس و اجرای آن
    collector = ProxyCollector()
    await collector.initialize()
    await collector.run()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("برنامه توسط کاربر متوقف شد")
    except Exception as e:
        logger.error(f"خطای نهایی: {str(e)}")