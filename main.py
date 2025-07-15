 import os, json, asyncio, math, logging
from dotenv import load_dotenv
from upstox import Upstox, MarketDataStreamerV3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()

BOT_TOKEN  = os.getenv("TG_TOKEN")
CHANNEL_ID = os.getenv("TG_CH")
API_KEY    = os.getenv("UP_API_KEY")
ACCESS     = os.getenv("UP_ACCESS")

LEVEL_FILE = "levels.json"
if not os.path.exists(LEVEL_FILE):
    json.dump([], open(LEVEL_FILE, "w"))

def _load():
    with open(LEVEL_FILE) as f:
        return json.load(f)

def _save(data):
    with open(LEVEL_FILE, "w") as f:
        json.dump(data, f)

async def add_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        _, sym, entry, sl, tgt = update.message.text.split()
        levels = _load()
        levels.append({
            "s": sym.upper(), "e": float(entry),
            "sl": float(sl), "t": float(tgt),
            "st": "wait", "p": None
        })
        _save(levels)
        await update.message.reply_text(
            f"✅ {sym.upper()} Added  (Entry {entry}, SL {sl}, Target {tgt})")
    except Exception:
        await update.message.reply_text("❌ Format: /add SYM ENTRY SL TARGET")

async def post_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.partition(' ')[2]
    if msg:
        await ctx.bot.send_message(CHANNEL_ID, msg)
        await update.message.reply_text("✅ Posted")
    else:
        await update.message.reply_text("❌ Usage: /post Your text")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("add", add_cmd))
    app.add_handler(CommandHandler("post", post_cmd))

    up = Upstox(API_KEY, ACCESS)
    instrument_map = {i.tradingsymbol: i.token for i in up.get_instruments()}
    streamer = MarketDataStreamerV3(access_token=ACCESS)

    async def on_tick(data):
        sym, ltp = data["tradingsymbol"], data["ltp"]
        lvls = _load()
        changed = False
        for lv in lvls:
            if lv["s"] != sym or lv["st"] == "closed":
                continue
            if lv["st"] == "wait" and ltp >= lv["e"]:
                lv.update(st="live", p=math.floor(ltp))
                await app.bot.send_message(CHANNEL_ID, f"🚀 Entry {sym} @₹{ltp}")
                changed = True
            elif lv["st"] == "live":
                if ltp >= lv["p"] + 1 and ltp < lv["t"]:
                    lv["p"] += 1
                    await app.bot.send_message(CHANNEL_ID, f"📈 {sym} ₹{ltp}")
                    changed = True
                if ltp >= lv["t"]:
                    lv["st"] = "closed"
                    await app.bot.send_message(CHANNEL_ID, f"🎯 Target {sym} @₹{ltp}")
                    changed = True
                elif ltp <= lv["sl"]:
                    lv["st"] = "closed"
                    await app.bot.send_message(CHANNEL_ID, f"🛑 SL {sym} @₹{ltp}")
                    changed = True
        if changed:
            _save(lvls)

    tokens = [instrument_map[x["s"]] for x in _load() if x["s"] in instrument_map]
    if tokens:
        streamer.subscribe(tokens)
        streamer.start_stream(callback=on_tick)

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("✅ Upstox SDK loaded OK")
    asyncio.run(main())
