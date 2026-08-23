# Amul Whey Protein stock bot

Checks the Amul shop every ~15 minutes via GitHub Actions and pings you on
**Telegram** and/or **WhatsApp** when the product flips from sold-out to in-stock.

No server needed — it runs free on GitHub Actions.

---

## 1. Create the repo

On the GitHub account you want to use:

1. Create a **new repository** (private is fine).
2. Add these files to it (same paths as here):
   - `check_amul.py`
   - `state.json`
   - `requirements.txt`
   - `.github/workflows/amul-watch.yml`
3. Commit / push.

## 2. Set up Telegram (required)

1. In Telegram, message **@BotFather** → `/newbot` → copy the **bot token**.
2. Send your new bot any message ("hi").
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` in a browser and copy
   the `chat.id` number from the JSON.

## 3. Set up WhatsApp via Twilio (optional)

1. Sign up at twilio.com and open the **WhatsApp sandbox**
   (Console → Messaging → Try it out → Send a WhatsApp message).
2. From your phone, send the shown `join <code>` message to the sandbox number.
3. Note your **Account SID**, **Auth Token**, the **sandbox From number**
   (looks like `whatsapp:+14155238886`), and your own number as
   `whatsapp:+91XXXXXXXXXX`.

> Sandbox note: Twilio's free WhatsApp sandbox stops delivering if you don't
> re-message it every 72 hours (24h in some regions). For a permanent setup
> you'd move to an approved WhatsApp sender, but the sandbox is fine to start.

## 4. Add the secrets to GitHub

Repo → **Settings → Secrets and variables → Actions → New repository secret**.
Add:

| Secret name    | Value                                   | Required |
|----------------|-----------------------------------------|----------|
| `TG_BOT_TOKEN` | Telegram bot token                      | ✅ |
| `TG_CHAT_ID`   | Your Telegram chat id                   | ✅ |
| `TWILIO_SID`   | Twilio Account SID                      | for WhatsApp |
| `TWILIO_TOKEN` | Twilio Auth Token                       | for WhatsApp |
| `TWILIO_FROM`  | `whatsapp:+14155238886` (sandbox)       | for WhatsApp |
| `TWILIO_TO`    | `whatsapp:+91XXXXXXXXXX` (your number)  | for WhatsApp |

Leave the Twilio ones out if you only want Telegram — the script skips WhatsApp
when they're absent.

## 5. Turn it on & test

- Repo → **Actions** tab → enable workflows if prompted.
- Open **"Amul stock watch"** → **Run workflow** (manual trigger) to test now.
- Check the run log: it prints `was_in_stock=… now_in_stock=…`. When the product
  is available you'll get the Telegram/WhatsApp ping.

The schedule (`*/15 * * * *`) then runs it automatically. Change that line in the
workflow to adjust frequency (don't go below ~10 min).

## How it avoids spam

Each run compares against `state.json` (committed back by the workflow) and only
notifies on the **transition** sold-out → in-stock — not on every run while it
stays in stock.

## Changing the product

Edit `PRODUCT_URL` and `PRODUCT_NAME` at the top of `check_amul.py`. To watch
several products, duplicate the check logic per URL (ask and I'll wire it up).
