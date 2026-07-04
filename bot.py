import os
import io
import logging
import zipfile
from datetime import datetime

from dotenv import load_dotenv
from PIL import Image
from telegram import Update, InputFile
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set")

# Favicon size specs
ICO_SIZES = [(16, 16), (32, 32), (48, 48)]
PNG_SIZES = {
    "favicon-16x16.png": (16, 16),
    "favicon-32x32.png": (32, 32),
    "apple-touch-icon.png": (180, 180),
    "android-chrome-192x192.png": (192, 192),
    "android-chrome-512x512.png": (512, 512),
}

WEBMANIFEST_TEMPLATE = """{
  "name": "",
  "short_name": "",
  "icons": [
    {
      "src": "/android-chrome-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/android-chrome-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ],
  "theme_color": "#ffffff",
  "background_color": "#ffffff",
  "display": "standalone"
}
"""

HTML_SNIPPET = """<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="manifest" href="/site.webmanifest">
"""


def make_square(img: Image.Image) -> Image.Image:
    """Pad a non-square image onto a transparent square canvas (no distortion)."""
    img = img.convert("RGBA")
    w, h = img.size
    if w == h:
        return img
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas


def generate_favicon_package(source_bytes: bytes) -> io.BytesIO:
    """Generate a zip file containing all favicon assets from source image bytes."""
    img = Image.open(io.BytesIO(source_bytes))
    img = make_square(img)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # PNG favicons at each required size
        for filename, size in PNG_SIZES.items():
            resized = img.resize(size, Image.LANCZOS)
            buf = io.BytesIO()
            resized.save(buf, format="PNG")
            zf.writestr(filename, buf.getvalue())

        # Multi-resolution .ico
        ico_buf = io.BytesIO()
        base_for_ico = img.resize((256, 256), Image.LANCZOS)
        base_for_ico.save(ico_buf, format="ICO", sizes=ICO_SIZES)
        zf.writestr("favicon.ico", ico_buf.getvalue())

        # Web app manifest + usage snippet
        zf.writestr("site.webmanifest", WEBMANIFEST_TEMPLATE)
        zf.writestr("head-snippet.html", HTML_SNIPPET)

    zip_buffer.seek(0)
    return zip_buffer


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi! I'm a Favicon Generator bot.\n\n"
        "Send me an image (PNG/JPG/WEBP, ideally at least 512x512) and I'll "
        "generate a full favicon package for your website:\n\n"
        "• favicon.ico (16/32/48px)\n"
        "• favicon-16x16.png\n"
        "• favicon-32x32.png\n"
        "• apple-touch-icon.png (180x180)\n"
        "• android-chrome-192x192.png\n"
        "• android-chrome-512x512.png\n"
        "• site.webmanifest\n"
        "• HTML snippet for your <head>\n\n"
        "Just send the image now 📤"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.UPLOAD_DOCUMENT)

    try:
        if message.photo:
            tg_file = await message.photo[-1].get_file()
        elif (
            message.document
            and message.document.mime_type
            and message.document.mime_type.startswith("image/")
        ):
            tg_file = await message.document.get_file()
        else:
            await message.reply_text("Please send an image file (PNG, JPG, or WEBP).")
            return

        file_bytes = await tg_file.download_as_bytearray()
        zip_buffer = generate_favicon_package(bytes(file_bytes))

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        await message.reply_document(
            document=InputFile(zip_buffer, filename=f"favicon-package-{timestamp}.zip"),
            caption=(
                "✅ Here's your favicon package!\n\n"
                "Unzip it, drop the files in the root of your website, and paste "
                "the contents of head-snippet.html into your <head> tag."
            ),
        )
    except Exception:
        logger.exception("Failed to generate favicon")
        await message.reply_text(
            "⚠️ Sorry, something went wrong while processing that image. "
            "Please try a different image (PNG/JPG)."
        )


async def handle_other(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send me an image to generate a favicon package 🖼️")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))
    app.add_handler(MessageHandler(~filters.COMMAND, handle_other))

    logger.info("Favicon bot starting (polling)...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
