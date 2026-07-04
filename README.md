# Favicon Generator Telegram Bot

A Telegram bot that turns any image into a complete favicon package
(`.ico`, PNGs at every standard size, a `site.webmanifest`, and an
HTML snippet) — deployed as a **Render Background Worker**.

## What it does

1. User sends a photo/image to the bot.
2. Bot pads it to a square (if needed) and generates:
   - `favicon.ico` (16/32/48 px, multi-resolution)
   - `favicon-16x16.png`
   - `favicon-32x32.png`
   - `apple-touch-icon.png` (180x180)
   - `android-chrome-192x192.png`
   - `android-chrome-512x512.png`
   - `site.webmanifest`
   - `head-snippet.html` (ready-to-paste `<head>` tags)
3. Bot zips everything and sends it back as a document.

## 1. Create the Telegram bot

1. Open Telegram, message **@BotFather**.
2. Send `/newbot` and follow the prompts.
3. Copy the token it gives you (looks like `123456789:ABCdefGhIJKlmNoPQRstuVWXyz`).

## 2. Run locally (optional, to test first)

```bash
git clone <your-repo-url>
cd favicon-bot
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your token into TELEGRAM_BOT_TOKEN
python bot.py
```

Open Telegram, message your bot, send `/start`, then send it an image.

## 3. Push to GitHub

```bash
git init
git add .
git commit -m "Favicon generator telegram bot"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

> `.env` is already in `.gitignore` — never commit your real token.

## 4. Deploy on Render (Background Worker)

**Option A — one-click via Blueprint (`render.yaml`, included in this repo):**

1. Go to [Render Dashboard](https://dashboard.render.com/).
2. Click **New → Blueprint**.
3. Connect your GitHub repo. Render will detect `render.yaml` automatically.
4. When prompted, set the environment variable:
   - `TELEGRAM_BOT_TOKEN` = your bot token from BotFather
5. Click **Apply**. Render will build and start the worker.

**Option B — manual setup:**

1. Go to [Render Dashboard](https://dashboard.render.com/) → **New → Background Worker**.
2. Connect your GitHub repo.
3. Settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
4. Under **Environment Variables**, add:
   - `TELEGRAM_BOT_TOKEN` = your bot token
5. Click **Create Background Worker**.

That's it — since this uses long-polling (`run_polling`), a Background
Worker is the right service type (no public URL/port needed, unlike a Web Service).

## 5. Verify it's alive

Check the Render logs for:

```
Favicon bot starting (polling)...
```

Then message your bot on Telegram with `/start` or an image.

## Notes / possible extensions

- Non-square images are padded onto a transparent square canvas rather than
  cropped, so nothing important gets cut off.
- To support very large images faster, you could downscale before processing.
- If you'd rather use webhooks instead of polling, you'd need a **Web Service**
  (not a Background Worker) since webhooks require an HTTP endpoint.
