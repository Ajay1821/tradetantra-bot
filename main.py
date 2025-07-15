
import os, json, asyncio, math, logging
from dotenv import load_dotenv
try:
    from upstox_sdk import Upstox, MarketDataStreamerV3
except ModuleNotFoundError:
    from upstox_python_sdk import Upstox, MarketDataStreamerV3
print("✅ Upstox SDK loaded OK")
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()  # reads .env

BOT_TOKEN   = os.getenv("TG_TOKEN")
CHANNEL_ID  = os.getenv("TG_CH")
API_KEY     = os.getenv("UP_API_KEY")
ACCESS      = os.getenv("UP_ACCESS")

if not all([BOT_TOKEN, CHANNEL_ID, API_KEY, ACCESS]):
    raise RuntimeError("Missing env variables. Check .env file.")

LEVEL_FILE = "levels.json"
if not os.path.exists(LEVEL_FILE):
    with open(LEVEL_FILE, "w") as f:
        json.dump([], f)

def load_levels():
    with open(LEVEL_FILE) as f:
        return json.load(f)

def save_levels(data):
    with open(LEVEL_FILE, "w") as f:
        json.dump(data, f)

async def add_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # /add SYMBOL entry sl target  (fixed order)
    try:
        parts = update.message.text.split()
        _, sym, entry, sl, tgt = parts
        lvls = load_levels()
        lvls.append({"s": sym.upper(),
                     "e": float(entry),
                     "sl": float(sl),
                     "t": float(tgt),
                     "st": "wait",
                     "last": None})
        save_levels(lvls)
        await update.message.reply_text(f"✅ Added {sym.upper()} (Entry {entry}, SL {sl}, Target {tgt})")
    except Exception as e:
        await update.message.reply_text("❌ Format: /add SYMBOL ENTRY SL TARGET")

async def post_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # /post message text
    msg = update.message.text.partition(' ')[2]
    if msg:
        await ctx.bot.send_message(CHANNEL_ID, msg)
        await update.message.reply_text("✅ Posted to channel.")
    else:
        await update.message.reply_text("❌ Usage: /post Your message")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("add", add_cmd))
    app.add_handler(CommandHandler("post", post_cmd))

    # Upstox live price
    u = Upstox(API_KEY, ACCESS)
    instruments = {i.tradingsymbol: i.token for i in u.get_instruments()}
    stream = MarketDataStreamerV3(access_token=ACCESS)

    async def on_tick(data):
        sym = data["tradingsymbol"]
        ltp = data["ltp"]
        levels = load_levels()
        changed = False
        for lv in levels:
            if lv["s"] != sym or lv["st"] == "closed":
                continue
            if lv["st"] == "wait" and ltp >= lv["e"]:
                lv["st"] = "active"
                lv["last"] = math.floor(ltp)
                await app.bot.send_message(CHANNEL_ID, f"🚀 Entry Triggered {sym} @ ₹{ltp}")
                changed = True
            elif lv["st"] == "active":
                if ltp >= lv["last"] + 1 and ltp < lv["t"]:
                    lv["last"] += 1
                    await app.bot.send_message(CHANNEL_ID, f"📈 {sym} ₹{ltp}")
                    changed = True
                if ltp >= lv["t"]:
                    lv["st"] = "closed"
                    await app.bot.send_message(CHANNEL_ID, f"🎯 Target Achieved {sym} @ ₹{ltp}")
                    changed = True
                elif ltp <= lv["sl"]:
                    lv["st"] = "closed"
                    await app.bot.send_message(CHANNEL_ID, f"🛑 Stoploss Hit {sym} @ ₹{ltp}")
                    changed = True
        if changed:
            save_levels(levels)

    subs = []
    for lv in load_levels():
        if lv["s"] in instruments:
            subs.append(instruments[lv["s"]])
    if subs:
        stream.subscribe(subs)
        stream.start_stream(callback=on_tick)

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    asyncio.run(main())
