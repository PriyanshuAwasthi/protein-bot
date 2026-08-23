#!/usr/bin/env python3
"""One-shot Amul stock check for GitHub Actions.

Renders the product page with a headless browser, and on a transition from
sold-out -> in-stock sends a Telegram message and (optionally) a WhatsApp
message via Twilio. State is persisted in state.json (committed back by the
workflow) so we don't re-alert on every run.

Env vars (set as GitHub Actions secrets):
  TG_BOT_TOKEN     Telegram bot token          (required for Telegram)
  TG_CHAT_ID       Telegram chat id            (required for Telegram)
  TWILIO_SID       Twilio Account SID          (optional -> enables WhatsApp)
  TWILIO_TOKEN     Twilio Auth Token           (optional)
  TWILIO_FROM      e.g. whatsapp:+14155238886  (Twilio sandbox number)
  TWILIO_TO        e.g. whatsapp:+9198XXXXXXXX (your number)
"""
import json
import os
import sys
import requests
from playwright.sync_api import sync_playwright

PRODUCT_URL = "https://shop.amul.com/en/product/amul-whey-protein-32-g-or-pack-of-60-sachets"
PRODUCT_NAME = "Amul Whey Protein (60 sachets)"
STATE_FILE = "state.json"


def check_stock() -> bool:
    """Return True if the product looks purchasable right now."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0 Safari/537.36"
        )
        try:
            page.goto(PRODUCT_URL, wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(2500)  # let the product widget hydrate
            body = page.inner_text("body").lower()
        finally:
            browser.close()

    sold_out = ("sold out" in body) or ("out of stock" in body) or ("notify me" in body)
    can_buy = "add to cart" in body
    return can_buy and not sold_out


def send_telegram(message: str) -> None:
    token, chat = os.environ.get("TG_BOT_TOKEN"), os.environ.get("TG_CHAT_ID")
    if not (token and chat):
        print("Telegram not configured; skipping.")
        return
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat, "text": message},
        timeout=20,
    )
    print(f"Telegram send -> {r.status_code}")


def send_whatsapp(message: str) -> None:
    sid = os.environ.get("TWILIO_SID")
    token = os.environ.get("TWILIO_TOKEN")
    wa_from = os.environ.get("TWILIO_FROM")
    wa_to = os.environ.get("TWILIO_TO")
    if not all([sid, token, wa_from, wa_to]):
        print("WhatsApp/Twilio not configured; skipping.")
        return
    # Twilio REST API via plain HTTP (no SDK dependency needed).
    r = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        data={"From": wa_from, "To": wa_to, "Body": message},
        auth=(sid, token),
        timeout=20,
    )
    print(f"WhatsApp send -> {r.status_code}")


def load_state() -> dict:
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"in_stock": False}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def main() -> None:
    prev = load_state()
    was_in_stock = bool(prev.get("in_stock", False))

    try:
        in_stock = check_stock()
    except Exception as e:
        # Don't flip state on a transient failure; just log and exit clean.
        print(f"check failed: {e}")
        sys.exit(0)

    print(f"was_in_stock={was_in_stock}  now_in_stock={in_stock}")

    if in_stock and not was_in_stock:
        msg = f"🟢 {PRODUCT_NAME} is IN STOCK!\nBuy now: {PRODUCT_URL}"
        send_telegram(msg)
        send_whatsapp(msg)

    save_state({"in_stock": in_stock})


if __name__ == "__main__":
    main()
