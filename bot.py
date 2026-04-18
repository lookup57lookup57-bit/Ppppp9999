import telebot
import os
import re
import json
import requests
import time
import random
import string
import threading
from telebot import types
from gatet import chkk
from reg import reg
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════
token = "8039312180:AAGI2t11_8PjNc6hFJwHK4FlRnojiUGfD0w"          # 🔴 PASTE YOUR BOT TOKEN HERE
admin = 7935621079         # 🔴 PASTE YOUR ADMIN ID HERE

bot = telebot.TeleBot(token, parse_mode="HTML")

# ═══════════════════════════════════════════════════════════════
# STATE MANAGEMENT
# ═══════════════════════════════════════════════════════════════
stopuser = {}
active_scans = set()
command_usage = {}

# ═══════════════════════════════════════════════════════════════
# FONT HELPER — Premium Unicode Sans-Serif Bold
# ═══════════════════════════════════════════════════════════════
def _b(text):
    """Convert to Mathematical Sans-Serif Bold"""
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold   = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    return text.translate(str.maketrans(normal, bold))

# ═══════════════════════════════════════════════════════════════
# BIN LOOKUP
# ═══════════════════════════════════════════════════════════════
def dato(zh):
    try:
        api_url = requests.get("https://bins.antipublic.cc/bins/" + zh).json()
        brand = api_url.get("brand", "N/A")
        card_type = api_url.get("type", "N/A")
        level = api_url.get("level", "N/A")
        bank = api_url.get("bank", "N/A")
        country_name = api_url.get("country_name", "N/A")
        country_flag = api_url.get("country_flag", "")
        return f"• BIN Info : {brand} - {card_type} - {level}\n• Bank : {bank} - {country_flag}\n• Country : {country_name} [ {country_flag} ]"
    except Exception as e:
        return "No info"

# ═══════════════════════════════════════════════════════════════
# /START COMMAND
# ═══════════════════════════════════════════════════════════════
@bot.message_handler(commands=["start"])
def start(message):
    def my_function():
        name = message.from_user.first_name
        user_id = message.from_user.id

        # Ensure user exists in database
        try:
            with open('data.json', 'r') as file:
                json_data = json.load(file)
        except:
            json_data = {}

        if str(user_id) not in json_data:
            json_data[str(user_id)] = {"plan": "𝗙𝗥𝗘𝗘", "timer": "none"}
            with open('data.json', 'w') as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)

        plan = json_data[str(user_id)].get("plan", "𝗙𝗥𝗘𝗘")

        if plan == "𝗙𝗥𝗘𝗘":
            keyboard = types.InlineKeyboardMarkup()
            contact_button = types.InlineKeyboardButton(text="✨ 𝗝𝗢𝗜𝗡 ✨", url="https://t.me/+WwjBeTcnFz0yZWVi")
            keyboard.add(contact_button)
            bot.send_message(
                chat_id=message.chat.id,
                text=f'''<b>
👋 Welcome, {name}!

🔒 This bot is premium and not free.
💰 Subscription Price: $2 per day
📞 For subscription & support: @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙
</b>''',
                reply_markup=keyboard
            )
            return

        # VIP User
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="✨ 𝗝𝗢𝗜𝗡 ✨", url="https://t.me/+WwjBeTcnFz0yZWVi")
        keyboard.add(contact_button)
        bot.send_message(
            chat_id=message.chat.id,
            text='''<b>
✅ Your subscription is active!

📁 Send me your file to check
💳 Or use manual check:
<code>/chk CC|MM|YY|CVV</code>
</b>''',
            reply_markup=keyboard
        )

    my_thread = threading.Thread(target=my_function)
    my_thread.start()

# ═══════════════════════════════════════════════════════════════
# /CMDS COMMAND
# ═══════════════════════════════════════════════════════════════
@bot.message_handler(commands=["cmds"])
def cmds(message):
    user_id = message.from_user.id
    try:
        with open('data.json', 'r') as file:
            json_data = json.load(file)
        plan = json_data[str(user_id)].get("plan", "𝗙𝗥𝗘𝗘")
    except:
        plan = "𝗙𝗥𝗘𝗘"

    keyboard = types.InlineKeyboardMarkup()
    contact_button = types.InlineKeyboardButton(text=f"✨ {plan} ✨", callback_data='plan')
    keyboard.add(contact_button)

    bot.send_message(
        chat_id=message.chat.id,
        text=f'''<b>
{_b("Bot Commands")}

💳 PayPal Commerce $1 ✅
<code>/chk</code> number|mm|yy|cvv

🟢 STATUS : ONLINE
</b>''',
        reply_markup=keyboard
    )

# ═══════════════════════════════════════════════════════════════
# DOCUMENT HANDLER (File Upload)
# ═══════════════════════════════════════════════════════════════
@bot.message_handler(content_types=["document"])
def main(message):
    user_id = message.from_user.id

    # Load user data
    try:
        with open('data.json', 'r') as file:
            json_data = json.load(file)
    except:
        json_data = {}

    if str(user_id) not in json_data:
        json_data[str(user_id)] = {"plan": "𝗙𝗥𝗘𝗘", "timer": "none"}
        with open('data.json', 'w') as file:
            json.dump(json_data, file, ensure_ascii=False, indent=4)

    plan = json_data[str(user_id)].get("plan", "𝗙𝗥𝗘𝗘")

    if plan == "𝗙𝗥𝗘𝗘":
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙")
        keyboard.add(contact_button)
        bot.send_message(
            chat_id=message.chat.id,
            text='''<b>
👋 Welcome!

🔒 This bot is premium and not free.
💰 Subscription Price: $2 per day
📞 For subscription & support: @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙
</b>''',
            reply_markup=keyboard
        )
        return

    # Check timer expiry
    timer_val = json_data[str(user_id)].get("timer", "none")
    if timer_val == "none":
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙")
        keyboard.add(contact_button)
        bot.send_message(
            chat_id=message.chat.id,
            text='''<b>
👋 Welcome!

🔒 This bot is premium and not free.
💰 Subscription Price: $2 per day
📞 For subscription & support: @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙
</b>''',
            reply_markup=keyboard
        )
        return

    try:
        date_str = timer_val.split('.')[0]
        provided_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except:
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙")
        keyboard.add(contact_button)
        bot.send_message(
            chat_id=message.chat.id,
            text='''<b>
👋 Welcome!

🔒 This bot is premium and not free.
💰 Subscription Price: $2 per day
📞 For subscription & support: @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙
</b>''',
            reply_markup=keyboard
        )
        return

    current_time = datetime.now()
    if current_time > provided_time:
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙")
        keyboard.add(contact_button)
        bot.send_message(
            chat_id=message.chat.id,
            text='''<b>
⛔ Your subscription has expired!

💰 Renew your subscription: @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙
</b>''',
            reply_markup=keyboard
        )
        json_data[str(user_id)]["timer"] = "none"
        json_data[str(user_id)]["plan"] = "𝗙𝗥𝗘𝗘"
        with open('data.json', 'w') as file:
            json.dump(json_data, file, indent=2)
        return

    # Check active scan
    if user_id in active_scans:
        bot.reply_to(message, "<b>⚠️ You cannot check multiple files at once!\n\nPlease wait for the current scan to finish or stop it first.</b>")
        return
    else:
        active_scans.add(user_id)

    # Download file
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        with open("combo.txt", "wb") as f:
            f.write(downloaded)
    except Exception as e:
        bot.reply_to(message, f"<b>❌ Failed to download file: {e}</b>")
        active_scans.discard(user_id)
        return

    keyboard = types.InlineKeyboardMarkup()
    contact_button = types.InlineKeyboardButton(text="PayPal Commerce $1", callback_data='br')
    keyboard.add(contact_button)
    bot.reply_to(
        message,
        text='''<b>Choose the gateway you want to use</b>''',
        reply_markup=keyboard
    )

# ═══════════════════════════════════════════════════════════════
# GATEWAY CALLBACK (Mass Check)
# ═══════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda call: call.data == 'br')
def menu_callback(call):
    def my_function():
        user_id = call.from_user.id
        gate = "PayPal Commerce $1"
        dd = 0
        live = 0
        ccnn = 0

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f'''<b>⏳ Checking your cards at {gate} gateway...\n\n👑 Bot by @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙</b>'''
        )

        try:
            with open("combo.txt", 'r') as file:
                lino = file.readlines()
                total = len(lino)

                try:
                    stopuser[str(user_id)]["status"] = "start"
                except:
                    stopuser[str(user_id)] = {"status": "start"}

                for cc in lino:
                    cc = cc.strip()
                    if not cc:
                        continue

                    if stopuser[str(user_id)]["status"] == "stop":
                        bot.edit_message_text(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text='''<b>🛑 Stopped!\n\n👑 Bot by @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙</b>'''
                        )
                        return

                    info = str(dato(cc[:6]))
                    start_time = time.time()

                    try:
                        last = str(chkk(cc))
                    except Exception as e:
                        print(e)
                        last = "ERROR"

                    if 'risk' in last.lower():
                        last = "DECLINED ❌ | Risk Disallowed"
                    elif 'Duplicate' in last:
                        last = "Approved ✅ | Duplicate"

                    end_time = time.time()
                    execution_time = end_time - start_time

                    mes = types.InlineKeyboardMarkup(row_width=1)
                    cm1 = types.InlineKeyboardButton(f"• {cc} •", callback_data='u8')
                    status_btn = types.InlineKeyboardButton(f"• Response ➜ {last} •", callback_data='u8')
                    cm3 = types.InlineKeyboardButton(f"• Approved ✅ ➜ [ {live} ] •", callback_data='x')
                    ccn_btn = types.InlineKeyboardButton(f"• CCN ☑️ ➜ [ {ccnn} ] •", callback_data='x')
                    cm4 = types.InlineKeyboardButton(f"• Declined ❌ ➜ [ {dd} ] •", callback_data='x')
                    cm5 = types.InlineKeyboardButton(f"• Total 👻 ➜ [ {total} ] •", callback_data='x')
                    stop_btn = types.InlineKeyboardButton(f"[ Stop ]", callback_data='stop')
                    mes.add(cm1, status_btn, cm3, ccn_btn, cm4, cm5, stop_btn)

                    bot.edit_message_text(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=f'''<b>⏳ Checking your cards at {gate} gateway...\n\n👑 Bot by @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙</b>''',
                        reply_markup=mes
                    )

                    msgc = f'''<b>☑️ CCN

• Card : <code>{cc}</code>
• Response : {last}
• Gateway : {gate}
{info}
• Time : {"{:.1f}".format(execution_time)}s
• Bot By : @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙</b>'''

                    msg_live = f'''<b>✅ APPROVED

• Card : <code>{cc}</code>
• Response : {last}
• Gateway : {gate}
{info}
• Time : {"{:.1f}".format(execution_time)}s
• Bot By : @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙</b>'''

                    if "Charged" in last or "Funds" in last or "Approved" in last:
                        live += 1
                        bot.send_message(call.from_user.id, msg_live)
                    elif "security code is incorrect" in last:
                        ccnn += 1
                        bot.send_message(call.from_user.id, msgc)
                    else:
                        dd += 1

                    time.sleep(2)
        except Exception as e:
            print(e)
        finally:
            if user_id in active_scans:
                active_scans.remove(user_id)

        stopuser[str(user_id)]["status"] = "start"
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text='''<b>✅ Checking Completed!\n\n👑 Bot by @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙</b>'''
        )

    my_thread = threading.Thread(target=my_function)
    my_thread.start()

# ═══════════════════════════════════════════════════════════════
# /CHK COMMAND (Single Check)
# ═══════════════════════════════════════════════════════════════
@bot.message_handler(func=lambda message: message.text.lower().startswith('.chk') or message.text.lower().startswith('/chk'))
def respond_to_chk(message):
    gate = "PayPal Commerce $1"
    name = message.from_user.first_name
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Load and validate user
    try:
        with open('data.json', 'r') as file:
            json_data = json.load(file)
    except:
        json_data = {}

    if str(user_id) not in json_data:
        json_data[str(user_id)] = {"plan": "𝗙𝗥𝗘𝗘", "timer": "none"}
        with open('data.json', 'w') as file:
            json.dump(json_data, file, ensure_ascii=False, indent=4)

    plan = json_data[str(user_id)].get("plan", "𝗙𝗥𝗘𝗘")

    if plan == "𝗙𝗥𝗘𝗘":
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙")
        keyboard.add(contact_button)
        bot.send_message(
            chat_id=message.chat.id,
            text=f'''<b>
👋 Welcome, {name}!

🔒 This bot is premium and not free.
💰 Subscription Price: $2 per day
📞 For subscription & support: @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙
</b>''',
            reply_markup=keyboard
        )
        return

    # Check expiry
    timer_val = json_data[str(chat_id)].get("timer", "none")
    if timer_val == "none":
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙")
        keyboard.add(contact_button)
        bot.send_message(
            chat_id=message.chat.id,
            text=f'''<b>
👋 Welcome, {name}!

🔒 This bot is premium and not free.
💰 Subscription Price: $2 per day
📞 For subscription & support: @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙
</b>''',
            reply_markup=keyboard
        )
        return

    try:
        date_str = timer_val.split('.')[0]
        provided_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    except:
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙")
        keyboard.add(contact_button)
        bot.send_message(
            chat_id=message.chat.id,
            text=f'''<b>
👋 Welcome, {name}!

🔒 This bot is premium and not free.
💰 Subscription Price: $2 per day
📞 For subscription & support: @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙
</b>''',
            reply_markup=keyboard
        )
        return

    current_time = datetime.now()
    if current_time > provided_time:
        keyboard = types.InlineKeyboardMarkup()
        contact_button = types.InlineKeyboardButton(text="✨ 𝗢𝗪𝗡𝗘𝗥 ✨", url="https://t.me/𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙")
        keyboard.add(contact_button)
        bot.send_message(
            chat_id=message.chat.id,
            text='''<b>⛔ Your subscription has expired!\n\n💰 Renew: @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙</b>''',
            reply_markup=keyboard
        )
        json_data[str(chat_id)]["timer"] = "none"
        json_data[str(chat_id)]["plan"] = "𝗙𝗥𝗘𝗘"
        with open('data.json', 'w') as file:
            json.dump(json_data, file, indent=2)
        return

    # Rate limiter
    if user_id not in command_usage:
        command_usage[user_id] = {"last_time": None}

    if command_usage[user_id]["last_time"] is not None:
        time_diff = (current_time - command_usage[user_id]["last_time"]).seconds
        if time_diff < 10:
            bot.reply_to(message, f"<b>⏳ Please wait {10 - time_diff} seconds.</b>")
            return

    command_usage[user_id]["last_time"] = current_time

    ko = bot.reply_to(message, "<b>⏳ Checking your card...</b>").message_id

    try:
        cc = message.reply_to_message.text
    except:
        cc = message.text

    cc = str(reg(cc))
    if cc == "None":
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=ko,
            text='''<b>🚫 Invalid Format!

Use: CC|MM|YY|CVV</b>'''
        )
        return

    start_time = time.time()
    try:
        last = str(chkk(cc))
    except Exception as e:
        last = f"ERROR: {e}"

    info = dato(cc[:6])
    end_time = time.time()
    execution_time = end_time - start_time

    msgc = f'''<b>☑️ CCN

• Card : <code>{cc}</code>
• Response : {last}
• Gateway : {gate}
{info}
• Time : {"{:.1f}".format(execution_time)}s
• Bot By : @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙</b>'''

    msgd = f'''<b>❌ DECLINED

• Card : <code>{cc}</code>
• Response : {last}
• Gateway : {gate}
{info}
• Time : {"{:.1f}".format(execution_time)}s
• Bot By : @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙</b>'''

    msg_live = f'''<b>✅ APPROVED

• Card : <code>{cc}</code>
• Response : {last}
• Gateway : {gate}
{info}
• Time : {"{:.1f}".format(execution_time)}s
• Bot By : @𝙏𝙮𝙧𝙖𝙣𝙩_𝙓𝙙</b>'''

    if "Charged" in last or "Funds" in last or "Approved" in last:
        bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text=msg_live)
    elif "security code is incorrect" in last:
        bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text=msgc)
    else:
        bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text=msgd)

# ═══════════════════════════════════════════════════════════════
# /REDEEM COMMAND
# ═══════════════════════════════════════════════════════════════
@bot.message_handler(func=lambda message: message.text.lower().startswith('.redeem') or message.text.lower().startswith('/redeem'))
def respond_to_redeem(message):
    def my_function():
        try:
            code = message.text.split(' ')[1]
            with open('data.json', 'r') as file:
                json_data = json.load(file)

            timer = json_data[code]["time"]
            typ = json_data[code]["plan"]

            json_data[str(message.from_user.id)]["timer"] = timer
            json_data[str(message.from_user.id)]["plan"] = typ

            with open('data.json', 'w') as file:
                json.dump(json_data, file, indent=2)

            # Remove used code
            with open('data.json', 'r') as file:
                data = json.load(file)
            del data[code]
            with open('data.json', 'w') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

            msg = f'''<b>✅ Subscription Activated!\n\n⏳ Expires: {timer}</b>'''
            bot.reply_to(message, msg)
        except Exception as e:
            print("ERROR:", e)
            bot.reply_to(message, '''<b>❌ Invalid code or already redeemed!</b>''')

    my_thread = threading.Thread(target=my_function)
    my_thread.start()

# ═══════════════════════════════════════════════════════════════
# /CODE COMMAND (Admin Only)
# ═══════════════════════════════════════════════════════════════
@bot.message_handler(commands=["code"])
def code(message):
    def my_function():
        user_id = message.from_user.id
        if user_id != admin:
            bot.reply_to(message, "<b>⛔ Admin only!</b>")
            return

        try:
            hours = float(message.text.split(' ')[1])
        except:
            bot.reply_to(message, "<b>Usage: /code &lt;hours&gt;</b>")
            return

        try:
            with open('data.json', 'r') as file:
                existing_data = json.load(file)
        except:
            existing_data = {}

        characters = string.ascii_uppercase + string.digits
        pas = 'TOME-' + ''.join(random.choices(characters, k=4)) + '-' + ''.join(random.choices(characters, k=4)) + '-' + ''.join(random.choices(characters, k=4))

        current_time = datetime.now()
        expiry = current_time + timedelta(hours=hours)
        plan = "𝗩𝗜𝗣"
        parts = str(expiry).split(':')
        expiry_str = ':'.join(parts[:2])

        existing_data[pas] = {"plan": plan, "time": expiry_str}
        with open('data.json', 'w') as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=4)

        msg = f'''<b>
🎁 Subscription Code Generated!

🔑 <code>/redeem {pas}</code>
⏳ Valid for: {hours} hours

📌 Tap the code to copy, then send it to the bot.
</b>'''
        bot.reply_to(message, msg)

    my_thread = threading.Thread(target=my_function)
    my_thread.start()

# ═══════════════════════════════════════════════════════════════
# STOP BUTTON CALLBACK
# ═══════════════════════════════════════════════════════════════
@bot.callback_query_handler(func=lambda call: call.data == 'stop')
def stop_callback(call):
    user_id = call.from_user.id
    try:
        stopuser[str(user_id)]["status"] = "stop"
    except:
        stopuser[str(user_id)] = {"status": "stop"}
    bot.answer_callback_query(call.id, "🛑 Stopping...")

# ═══════════════════════════════════════════════════════════════
# BOT POLLING
# ═══════════════════════════════════════════════════════════════
print("✅ Bot Started | English UI | PayPal Commerce $1")
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Polling error: {e}")
        time.sleep(5)
