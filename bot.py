import sqlite3
import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================================
# 🔑 BOT TOKEN
# ================================

TOKEN = "8645580845:AAGiUeKFO6Qx4E8MkfqNriHI7rTn5llJym0"

# ================================
# 🧠 SESSION MEMORY
# ================================

sessions = {}

# ================================
# 🗄 DATABASE SETUP
# ================================

conn = sqlite3.connect("trades.db", check_same_thread=False)
cursor = conn.cursor()

# ---------- USERS TABLE ----------

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    name TEXT,
    username TEXT,
    joined_date TEXT
)
""")

# ---------- TRADES TABLE ----------

cursor.execute("""
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    date TEXT,
    buy_qty REAL,
    sell_qty REAL,
    avg_buy REAL,
    avg_sell REAL,
    profit REAL,
    roi REAL
)
""")

conn.commit()

# ================================
# 👤 REGISTER USER
# ================================

def register_user(user):

    user_id = user.id
    name = user.first_name
    username = user.username
    joined = str(datetime.date.today())

    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute(
            "INSERT INTO users (user_id,name,username,joined_date) VALUES (?,?,?,?)",
            (user_id, name, username, joined)
        )
        conn.commit()


# ================================
# 🧠 TRADING INSIGHT ENGINE
# ================================

def ai_insight(avg_buy, avg_sell):

    spread = avg_sell - avg_buy

    if spread < 2:
        return """
🧠 Trading Insight

⚠️ Spread is very small.

Profit potential was limited.
Try waiting for a better arbitrage window next time.
"""

    elif spread < 5:
        return """
🧠 Trading Insight

🟡 Decent spread.

Trade was acceptable but not very strong.
A slightly wider spread would improve profits.
"""

    elif spread < 10:
        return """
🧠 Trading Insight

🟢 Healthy arbitrage spread.

Nice trade. Increasing volume here
could scale your profits nicely.
"""

    else:
        return """
🧠 Trading Insight

🚀 Excellent spread detected!

This was a strong arbitrage opportunity.
Trades like this can significantly boost
your daily profit.
"""

# ================================
# 🚀 START COMMAND
# ================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    register_user(update.effective_user)

    name = update.effective_user.first_name

    keyboard = [
        [InlineKeyboardButton("📊 New Trade", callback_data="new_trade")],
        [InlineKeyboardButton("📜 Trade History", callback_data="history")],
        [InlineKeyboardButton("📅 Last X Days", callback_data="days")],
        [InlineKeyboardButton("🏆 Best Trade", callback_data="best_trade")],
        [InlineKeyboardButton("💰 Total Profit", callback_data="profit")],
        [InlineKeyboardButton("⚡ Opportunity Calculator", callback_data="calc")],
        [InlineKeyboardButton("🤖 About Bot", callback_data="about")]
    ]

    await update.message.reply_text(
f"""
👋 Hey {name}!

🚀 Welcome to your *USDT Trading Assistant*

This bot helps you:

📊 Track your trades  
💰 Calculate profit automatically  
📈 Analyze arbitrage spreads  
📂 Store your trading history  

Tap a button below to begin 👇
""",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ================================
# 🎛 BUTTON HANDLER
# ================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id


    # -------- NEW TRADE --------
    if data == "new_trade":

        sessions[user_id] = {"step": "buy_count"}

        await query.edit_message_text(
"""
📊 Let's log today's trades!

🔢 How many times did you BUY USDT today?

(Max 15)
"""
        )


    # -------- TRADE HISTORY --------
    elif data == "history":

        cursor.execute(
            "SELECT date, profit FROM trades WHERE user_id=? ORDER BY id DESC LIMIT 5",
            (user_id,)
        )

        rows = cursor.fetchall()

        if not rows:
            await query.edit_message_text(
"""
📜 Trade History

No trades recorded yet.
"""
            )
            return

        text = "📜 Your Recent Trades\n\n"

        for r in rows:
            text += f"📅 {r[0]} → 💰 ₹{r[1]:.2f}\n"

        await query.edit_message_text(text)


    # -------- TOTAL PROFIT --------
    elif data == "profit":

        cursor.execute(
            "SELECT SUM(profit) FROM trades WHERE user_id=?",
            (user_id,)
        )

        result = cursor.fetchone()[0]

        if result is None:
            result = 0

        await query.edit_message_text(
f"""
💰 Total Profit

₹ {result:.2f}
"""
        )


    # -------- OPPORTUNITY CALCULATOR --------
    elif data == "calc":

        await query.edit_message_text(
"""
⚡ Opportunity Calculator

Send numbers like this:

Quantity BuyPrice SellPrice

Example:
1000 95 107
"""
        )


    # -------- BEST TRADE --------
    elif data == "best_trade":

        cursor.execute(
            "SELECT date, profit FROM trades WHERE user_id=? ORDER BY profit DESC LIMIT 1",
            (user_id,)
        )

        row = cursor.fetchone()

        if not row:
            await query.edit_message_text(
"""
🏆 Best Trade

No trades recorded yet.
"""
            )
            return

        await query.edit_message_text(
f"""
🏆 Best Trade

📅 Date: {row[0]}

💰 Profit: ₹{row[1]:.2f}
"""
        )


    # -------- LAST X DAYS --------
    elif data == "days":

        sessions[user_id] = {"step": "days_input"}

        await query.edit_message_text(
"""
📅 Last X Days Report

Enter number of days you want to analyze.

Example:
3
7
15
30

(Max 30)
"""
        )


    # -------- ABOUT BOT --------
    elif data == "about":

        keyboard = [
            [InlineKeyboardButton("📊 New Trade", callback_data="new_trade")],
            [InlineKeyboardButton("📜 Trade History", callback_data="history")],
            [InlineKeyboardButton("📅 Last X Days", callback_data="days")],
            [InlineKeyboardButton("🏆 Best Trade", callback_data="best_trade")],
            [InlineKeyboardButton("💰 Total Profit", callback_data="profit")]
        ]

        await query.edit_message_text(
"""
🤖 About This Bot

Welcome to your USDT Trading Assistant.

This bot tracks your trades,
calculates profit,
and saves you from doing painful math in your head.

Built with curiosity, caffeine
and a slightly dangerous amount of ambition.

⚡ Created by
@greatvelocity
""",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ================================
# 💬 MESSAGE HANDLER
# ================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    username = update.effective_user.first_name
    text = update.message.text.strip()


    # -------- OPPORTUNITY CALCULATOR --------

    parts = text.split()

    if len(parts) == 3:

        try:
            qty = float(parts[0])
            buy = float(parts[1])
            sell = float(parts[2])

            profit = (sell - buy) * qty
            roi = ((sell - buy) / buy) * 100

            insight = ai_insight(buy, sell)

            await update.message.reply_text(
f"""
⚡ Arbitrage Result

📦 Quantity: {qty}
📉 Buy Price: {buy}
📈 Sell Price: {sell}

💰 Profit: ₹{profit:.2f}
📊 ROI: {roi:.2f}%

{insight}
"""
            )

            return

        except:
            pass


    # -------- SESSION CHECK --------

    if user_id not in sessions:
        return

    session = sessions[user_id]


    # -------- LAST X DAYS INPUT --------

    if session["step"] == "days_input":

        try:
            d = int(text)

            if d < 1 or d > 30:
                await update.message.reply_text(
"⚠ Please enter a number between 1 and 30."
                )
                return

            since = datetime.datetime.now() - datetime.timedelta(days=d)

            cursor.execute(
                "SELECT COUNT(*), SUM(profit) FROM trades WHERE user_id=? AND date>=?",
                (user_id, since.strftime("%Y-%m-%d"))
            )

            result = cursor.fetchone()

            trades = result[0]
            profit = result[1] if result[1] else 0

            await update.message.reply_text(
f"""
📊 Last {d} Days Performance

🔁 Trades Logged: {trades}

💰 Total Profit: ₹{profit:.2f}
"""
            )

            sessions.pop(user_id)

        except:
            await update.message.reply_text("⚠ Please enter a valid number.")

        return

# ================================
# 📊 TRADE CONVERSATION ENGINE
# ================================

    # -------- BUY COUNT --------

    if session["step"] == "buy_count":

        try:
            n = int(text)

            if n < 1 or n > 15:
                await update.message.reply_text(
"⚠ Please enter a number between 1 and 15."
                )
                return

            session["buy_count"] = n
            session["current"] = 1
            session["buys"] = []
            session["step"] = "buy_qty"

            await update.message.reply_text(
f"""
📦 Buy Trade #{session['current']}

💰 How much USDT did you buy?
"""
            )

        except:
            await update.message.reply_text("⚠ Enter a valid number.")


    # -------- BUY QUANTITY --------

    elif session["step"] == "buy_qty":

        try:
            session["temp_qty"] = float(text)
            session["step"] = "buy_price"

            await update.message.reply_text(
"💲 At what price did you buy 1 USDT?"
            )

        except:
            await update.message.reply_text("⚠ Enter a valid number.")


    # -------- BUY PRICE --------

    elif session["step"] == "buy_price":

        try:
            qty = session["temp_qty"]
            price = float(text)

            session["buys"].append((qty, price))

            if session["current"] < session["buy_count"]:

                session["current"] += 1
                session["step"] = "buy_qty"

                await update.message.reply_text(
f"""
📦 Buy Trade #{session['current']}

💰 How much USDT did you buy?
"""
                )

            else:

                session["step"] = "sell_count"

                await update.message.reply_text(
"""
📉 Now let's record your SELL trades.

How many times did you SELL USDT today?

(Max 15)
"""
                )

        except:
            await update.message.reply_text("⚠ Enter a valid number.")


    # -------- SELL COUNT --------

    elif session["step"] == "sell_count":

        try:
            n = int(text)

            if n < 1 or n > 15:
                await update.message.reply_text(
"⚠ Please enter a number between 1 and 15."
                )
                return

            session["sell_count"] = n
            session["current_sell"] = 1
            session["sells"] = []
            session["step"] = "sell_qty"

            await update.message.reply_text(
f"""
📦 Sell Trade #{session['current_sell']}

💰 How much USDT did you sell?
"""
            )

        except:
            await update.message.reply_text("⚠ Enter a valid number.")

# -------- SELL QUANTITY --------

    elif session["step"] == "sell_qty":

        try:
            session["temp_sell_qty"] = float(text)
            session["step"] = "sell_price"

            await update.message.reply_text(
"💲 At what price did you sell 1 USDT?"
            )

        except:
            await update.message.reply_text("⚠ Enter a valid number.")


    # -------- SELL PRICE --------

    elif session["step"] == "sell_price":

        try:
            qty = session["temp_sell_qty"]
            price = float(text)

            session["sells"].append((qty, price))

            if session["current_sell"] < session["sell_count"]:

                session["current_sell"] += 1
                session["step"] = "sell_qty"

                await update.message.reply_text(
f"""
📦 Sell Trade #{session['current_sell']}

💰 How much USDT did you sell?
"""
                )

            else:

                buys = session["buys"]
                sells = session["sells"]

                total_buy_qty = sum(q for q,p in buys)
                total_buy_cost = sum(q*p for q,p in buys)

                total_sell_qty = sum(q for q,p in sells)
                total_sell_value = sum(q*p for q,p in sells)

                avg_buy = total_buy_cost / total_buy_qty
                avg_sell = total_sell_value / total_sell_qty

                profit = total_sell_value - total_buy_cost
                roi = (profit / total_buy_cost) * 100

                insight = ai_insight(avg_buy, avg_sell)

                date = datetime.date.today().strftime("%Y-%m-%d")

                cursor.execute(
"""
INSERT INTO trades
(user_id, username, date, buy_qty, sell_qty, avg_buy, avg_sell, profit, roi)
VALUES (?,?,?,?,?,?,?,?,?)
""",
(
user_id,
username,
date,
total_buy_qty,
total_sell_qty,
avg_buy,
avg_sell,
profit,
roi
)
                )

                conn.commit()

                keyboard = [
                    [InlineKeyboardButton("📊 New Trade", callback_data="new_trade")],
                    [InlineKeyboardButton("📜 History", callback_data="history")],
                    [InlineKeyboardButton("📅 Last X Days", callback_data="days")],
                    [InlineKeyboardButton("🏆 Best Trade", callback_data="best_trade")],
                    [InlineKeyboardButton("💰 Total Profit", callback_data="profit")]
                ]

                await update.message.reply_text(
f"""
📊 TRADE SUMMARY

💰 Total Bought: {total_buy_qty} USDT
📤 Total Sold: {total_sell_qty} USDT

📉 Avg Buy: {avg_buy:.2f}
📈 Avg Sell: {avg_sell:.2f}

💵 Profit: ₹{profit:.2f}
📊 ROI: {roi:.2f}%

{insight}
""",
reply_markup=InlineKeyboardMarkup(keyboard)
)

                sessions.pop(user_id)

        except:
            await update.message.reply_text("⚠ Enter a valid number.")

# ================================
# 🤖 BOT STARTUP
# ================================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(CallbackQueryHandler(buttons))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🚀 USDT Trading Assistant is running...")

app.run_polling()

