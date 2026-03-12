import sqlite3
import datetime
import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================================
# 🔑 BOT TOKEN
# =========================================

TOKEN = "8645580845:AAGiUeKFO6Qx4E8MkfqNriHI7rTn5llJym0"

# =========================================
# 👑 ADMIN SYSTEM
# =========================================

ADMIN_ID = @greatvelocity# replace with your telegram id

# =========================================
# 🧠 SESSION MEMORY
# =========================================

sessions = {}

# =========================================
# 🗄 DATABASE CONNECTION
# =========================================

conn = sqlite3.connect("trade_data.db", check_same_thread=False)
cursor = conn.cursor()

# =========================================
# 👥 USERS TABLE
# =========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER UNIQUE,
name TEXT,
username TEXT,
joined_date TEXT
)
""")

# =========================================
# 📊 TRADES TABLE
# =========================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS trades(
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

# =========================================
# 👤 REGISTER USER
# =========================================

def register_user(user):

    user_id = user.id
    name = user.first_name
    username = user.username
    joined = str(datetime.date.today())

    cursor.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    )

    exists = cursor.fetchone()

    if not exists:

        cursor.execute(
            "INSERT INTO users (user_id,name,username,joined_date) VALUES (?,?,?,?)",
            (user_id,name,username,joined)
        )

        conn.commit()

# =========================================
# 🧠 TRADING INSIGHT ENGINE
# =========================================

def ai_insight(avg_buy, avg_sell):

    spread = avg_sell - avg_buy

    if spread < 2:

        return """
⚠ Weak Spread

Profit potential was limited.
Better opportunities usually appear above ₹5 spread.
"""

    elif spread < 5:

        return """
🟡 Decent Spread

Trade was okay but not very strong.
Slightly larger spreads could improve profits.
"""

    elif spread < 10:

        return """
🟢 Healthy Arbitrage

Nice trade.
Scaling volume in these spreads can increase profits.
"""

    else:

        return """
🚀 Excellent Spread

This was a powerful arbitrage opportunity.
Trades like this can significantly boost daily profit.
"""

# =========================================
# 🚀 START COMMAND (TRADE DASHBOARD)
# =========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    register_user(user)

    name = user.first_name
    user_id = user.id

    # --- Today profit summary ---

    today = datetime.date.today().strftime("%Y-%m-%d")

    cursor.execute(
        "SELECT SUM(profit) FROM trades WHERE user_id=? AND date=?",
        (user_id,today)
    )

    today_profit = cursor.fetchone()[0]

    if today_profit is None:
        today_profit = 0

    # --- Dashboard Buttons ---

    keyboard = [

        [
            InlineKeyboardButton("📊 New Trade", callback_data="new_trade"),
            InlineKeyboardButton("📜 History", callback_data="history")
        ],

        [
            InlineKeyboardButton("📈 Analytics", callback_data="analytics"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
        ],

        [
            InlineKeyboardButton("⚡ Calculator", callback_data="calc"),
            InlineKeyboardButton("📅 Reports", callback_data="reports")
        ],

        [
            InlineKeyboardButton("🤖 About Bot", callback_data="about")
        ]

    ]

    await update.message.reply_text(

f"""
🚀 *Velocity Trade Terminal*

Welcome back **{name}**

━━━━━━━━━━━━━━━━━━

📊 *Today Snapshot*

💰 Profit Today: ₹{today_profit:.2f}

━━━━━━━━━━━━━━━━━━

Your personal **USDT trading assistant**
is ready.

Select an action below 👇
""",

    parse_mode="Markdown",
    reply_markup=InlineKeyboardMarkup(keyboard)

    )

# =========================================
# 🎛 BUTTON CONTROL SYSTEM
# =========================================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id


# =========================================
# 📊 NEW TRADE
# =========================================

    if data == "new_trade":

        sessions[user_id] = {"step": "buy_count"}

        keyboard = [
            [InlineKeyboardButton("❌ Cancel Trade", callback_data="cancel_trade")]
        ]

        await query.edit_message_text(

"""
📊 *Start New Trade*

How many BUY deals did you execute today?

(Max 15)
""",

        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)

        )


# =========================================
# ❌ CANCEL TRADE
# =========================================

    elif data == "cancel_trade":

        if user_id in sessions:
            sessions.pop(user_id)

        await query.edit_message_text(

"""
❌ Trade cancelled.

You can start again anytime.
"""
        )


# =========================================
# 📜 HISTORY
# =========================================

    elif data == "history":

        cursor.execute(
            "SELECT date,profit FROM trades WHERE user_id=? ORDER BY id DESC LIMIT 5",
            (user_id,)
        )

        rows = cursor.fetchall()

        if not rows:

            await query.edit_message_text(
"""
📜 No trades recorded yet.
"""
            )

            return


        text = "📜 *Recent Trades*\n\n"

        for r in rows:

            text += f"📅 {r[0]} → 💰 ₹{r[1]:.2f}\n"

        await query.edit_message_text(
            text,
            parse_mode="Markdown"
        )


# =========================================
# ⚡ OPPORTUNITY CALCULATOR
# =========================================

    elif data == "calc":

        await query.edit_message_text(

"""
⚡ *Arbitrage Calculator*

Send numbers like this:

Quantity BuyPrice SellPrice

Example:

1000 95 107
""",

        parse_mode="Markdown"

        )


# =========================================
# 📈 ANALYTICS
# =========================================

    elif data == "analytics":

        cursor.execute(
            "SELECT SUM(profit), COUNT(*) FROM trades WHERE user_id=?",
            (user_id,)
        )

        result = cursor.fetchone()

        profit = result[0] if result[0] else 0
        trades = result[1]

        await query.edit_message_text(

f"""
📊 *Trading Analytics*

💰 Lifetime Profit: ₹{profit:.2f}

📈 Total Trades: {trades}

Keep stacking spreads 🚀
""",

        parse_mode="Markdown"

        )


# =========================================
# 🏆 LEADERBOARD
# =========================================

    elif data == "leaderboard":

        cursor.execute(

"""
SELECT username, SUM(profit)
FROM trades
GROUP BY user_id
ORDER BY SUM(profit) DESC
LIMIT 5
"""
        )

        rows = cursor.fetchall()

        if not rows:

            await query.edit_message_text(
"""
🏆 Leaderboard empty.
"""
            )

            return

        text = "🏆 *Top Traders*\n\n"

        rank = 1

        for r in rows:

            user = r[0] if r[0] else "Trader"
            profit = r[1]

            text += f"{rank}️⃣ {user} — ₹{profit:.2f}\n"

            rank += 1


        await query.edit_message_text(
            text,
            parse_mode="Markdown"
        )


# =========================================
# 🤖 ABOUT
# =========================================

    elif data == "about":

        await query.edit_message_text(

"""
🤖 *Velocity Trade Bot*

Your personal **USDT trading assistant**.

Features:

📊 Trade logging
📈 Profit analytics
⚡ Arbitrage calculator
🏆 Leaderboard
📅 Performance reports

Built by:

🚀 @greatvelocity
""",

        parse_mode="Markdown"

        )

# =========================================
# 💬 MESSAGE HANDLER
# =========================================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    username = update.effective_user.first_name
    text = update.message.text.strip()


# =========================================
# ⚡ ARBITRAGE CALCULATOR
# =========================================

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


# =========================================
# SESSION CHECK
# =========================================

    if user_id not in sessions:
        return

    session = sessions[user_id]


# =========================================
# BUY COUNT
# =========================================

    if session["step"] == "buy_count":

        try:

            n = int(text)

            if n < 1 or n > 15:

                await update.message.reply_text(
"⚠ Enter number between 1 and 15"
                )

                return

            session["buy_count"] = n
            session["current"] = 1
            session["buys"] = []
            session["step"] = "buy_qty"

            await update.message.reply_text(

f"""
📦 Buy Trade #{session['current']}

How much USDT did you buy?
"""
            )

        except:

            await update.message.reply_text("⚠ Enter valid number")


# =========================================
# BUY QTY
# =========================================

    elif session["step"] == "buy_qty":

        try:

            session["temp_qty"] = float(text)
            session["step"] = "buy_price"

            await update.message.reply_text(
"💲 At what price did you buy 1 USDT?"
            )

        except:

            await update.message.reply_text("⚠ Enter valid number")


# =========================================
# BUY PRICE
# =========================================

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

How much USDT did you buy?
"""
                )

            else:

                session["step"] = "sell_count"

                await update.message.reply_text(

"""
📉 Now enter SELL trades

How many SELL deals today?
(Max 15)
"""
                )

        except:

            await update.message.reply_text("⚠ Enter valid number")


# =========================================
# SELL COUNT
# =========================================

    elif session["step"] == "sell_count":

        try:

            n = int(text)

            if n < 1 or n > 15:

                await update.message.reply_text(
"⚠ Enter number between 1 and 15"
                )

                return

            session["sell_count"] = n
            session["current_sell"] = 1
            session["sells"] = []
            session["step"] = "sell_qty"

            await update.message.reply_text(

f"""
📦 Sell Trade #{session['current_sell']}

How much USDT did you sell?
"""
            )

        except:

            await update.message.reply_text("⚠ Enter valid number")

# =========================================
# 📈 PROFIT GRAPH SYSTEM
# =========================================

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


async def profit_graph(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    cursor.execute(
        "SELECT date, profit FROM trades WHERE user_id=? ORDER BY date",
        (user_id,)
    )

    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text(
            "📊 No trade data available yet."
        )
        return

    dates = []
    profits = []

    for r in rows:
        dates.append(r[0])
        profits.append(r[1])

    plt.figure()

    plt.plot(dates, profits, marker="o")

    plt.title("Profit Trend")
    plt.xlabel("Date")
    plt.ylabel("Profit")

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig("profit_chart.png")
    plt.close()

    with open("profit_chart.png", "rb") as chart:
        await update.message.reply_photo(
            chart,
            caption="📈 Your Profit Performance"
        )


# =========================================
# 👑 ADMIN STATS
# =========================================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Admin only command.")
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM trades")
    trades = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(profit) FROM trades")
    profit = cursor.fetchone()[0]

    if profit is None:
        profit = 0

    await update.message.reply_text(

f"""
📊 BOT STATISTICS

👥 Total Users: {users}

📈 Total Trades: {trades}

💰 Total Profit Logged: ₹{profit:.2f}
"""
    )


# =========================================
# 🤖 BOT STARTUP
# =========================================

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("graph", profit_graph))

    # buttons
    app.add_handler(CallbackQueryHandler(buttons))

    # text handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Velocity Trade Bot running...")

    app.run_polling()


if __name__ == "__main__":
    main()

