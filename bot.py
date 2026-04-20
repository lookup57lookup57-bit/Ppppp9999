import telebot  
from telebot import types  
import os  
import time  
import requests  
import threading  
import re  
import json  
import random  
from datetime import datetime, timedelta  
from pp_gate import PayPal_1  

# ============================================
# CONFIGURATION
# ============================================
BOT_TOKEN = "8619822018:AAHEB8M2bqS2Yi-h8O1ftYpBrUuczwT1u8I"  
OWNER_ID = 7935621079 
OWNER_USERNAME = "Tyrant_Xd"  
OWNER_NAME = "𝙏𝙮𝙧𝙖𝙣𝙩"  

# Channels for sending results (leave empty to disable)
CHANNEL_FULL = ""  
CHANNEL_HITS = ""  

# Maximum cards allowed in combo file  
MAX_CARDS = 1500  

# Data file for subscriptions  
DATA_FILE = "subscriptions.json"  

bot = telebot.TeleBot(BOT_TOKEN)  

# Stop user dictionary for file checking  
stopuser = {}  

# Dictionary to track users currently checking files  
users_checking_files = {}  

# Anti-Spam: Track last check time for each user  
user_last_check_time = {}  
ANTI_SPAM_DELAY = 5  # seconds  

# ============================================  
# Subscription System  
# ============================================  

def read_data():  
    try:  
        if os.path.exists(DATA_FILE):  
            with open(DATA_FILE, 'r') as f:  
                return json.load(f)  
    except:  
        pass  
    return {}  

def write_data(data):  
    try:  
        with open(DATA_FILE, 'w') as f:  
            json.dump(data, f, indent=2, ensure_ascii=False)  
    except:  
        pass  

def ensure_user(user_id, first_name="User", username="NoUsername"):  
    data = read_data()  
    uid = str(user_id)  
    if uid not in data:  
        data[uid] = {  
            'first_name': first_name,  
            'username': username,  
            'points': 0,  
            'subscription_end': 0,  
            'total_checks': 0  
        }  
        write_data(data)  
    return data  

def has_subscription(user_id):  
    data = read_data()  
    uid = str(user_id)  
    if uid not in data:  
        return False  
    sub_end = max(  
        data[uid].get('subscription_end', 0),  
        data[uid].get('subscription_expiry', 0)  
    )  
    points = data[uid].get('points', 0)  
    return sub_end > time.time() or points > 0  

def get_remaining_time(user_id):  
    data = read_data()  
    uid = str(user_id)  
    if uid not in data:  
        return "No Subscription"  
    points = data[uid].get('points', 0)  
    if points > 0:  
        return f"{points} points"  
    sub_end = max(  
        data[uid].get('subscription_end', 0),  
        data[uid].get('subscription_expiry', 0)  
    )  
    if sub_end <= time.time():  
        return "Expired"  
    remaining = sub_end - time.time()  
    hours = int(remaining // 3600)  
    minutes = int((remaining % 3600) // 60)  
    return f"{hours}h {minutes}m"  

def add_subscription_time(user_id, hours):  
    data = read_data()  
    uid = str(user_id)  
    if uid not in data:  
        data[uid] = {'first_name': 'User', 'username': 'unknown', 'points': 0, 'subscription_end': 0, 'total_checks': 0}  
      
    current_time = time.time()  
    current_expiry = max(  
        data[uid].get('subscription_expiry', 0),  
        data[uid].get('subscription_end', 0)  
    )  
      
    if current_expiry > current_time:  
        new_expiry = current_expiry + (hours * 3600)  
    else:  
        new_expiry = current_time + (hours * 3600)  
      
    data[uid]['subscription_expiry'] = new_expiry  
    data[uid]['subscription_end'] = new_expiry  
    write_data(data)  
    return new_expiry  

def add_points(user_id, points):  
    data = read_data()  
    uid = str(user_id)  
    if uid not in data:  
        data[uid] = {'first_name': 'User', 'username': 'unknown', 'points': 0, 'subscription_end': 0, 'total_checks': 0}  
      
    data[uid]['points'] = data[uid].get('points', 0) + points  
    write_data(data)  
    return data[uid]['points']  

def deduct_points(user_id, amount=0.5):  
    data = read_data()  
    uid = str(user_id)  
    if uid not in data:  
        return False  
      
    points = data[uid].get('points', 0)  
    if points >= amount:  
        data[uid]['points'] = points - amount  
        write_data(data)  
        return True  
    return False  

def is_owner(user_id):  
    return user_id == OWNER_ID  

# ============================================  
# Reply Keyboard  
# ============================================  

def get_main_keyboard():  
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)  
    markup.add(  
        types.KeyboardButton("📁 Combo Check"),  
        types.KeyboardButton("💳 Single Check")  
    )  
    markup.add(  
        types.KeyboardButton("🔎 BIN Lookup"),  
        types.KeyboardButton("⭐ My Balance")  
    )  
    markup.add(  
        types.KeyboardButton("❓ Help"),  
        types.KeyboardButton("👨‍💻 Owner")  
    )  
    return markup  

# ============================================  
# BIN Lookup Functions  
# ============================================  

def get_country_flag(country_code):  
    flag_map = {  
        'US': '🇺🇸', 'GB': '🇬🇧', 'CA': '🇨🇦', 'AU': '🇦🇺', 'DE': '🇩🇪',  
        'FR': '🇫🇷', 'IT': '🇮🇹', 'ES': '🇪🇸', 'PT': '🇵🇹', 'NL': '🇳🇱',  
        'BE': '🇧🇪', 'CH': '🇨🇭', 'AT': '🇦🇹', 'SE': '🇸🇪', 'NO': '🇳🇴',  
        'DK': '🇩🇰', 'FI': '🇫🇮', 'IE': '🇮🇪', 'PL': '🇵🇱', 'CZ': '🇨🇿',  
        'GR': '🇬🇷', 'TR': '🇹🇷', 'AE': '🇦🇪', 'SA': '🇸🇦', 'EG': '🇪🇬',  
        'MA': '🇲🇦', 'ZA': '🇿🇦', 'IN': '🇮🇳', 'CN': '🇨🇳', 'JP': '🇯🇵',  
        'KR': '🇰🇷', 'RU': '🇷🇺', 'BR': '🇧🇷', 'MX': '🇲🇽', 'AR': '🇦🇷',  
        'ID': '🇮🇩', 'MY': '🇲🇾', 'SG': '🇸🇬', 'TH': '🇹🇭', 'VN': '🇻🇳',  
        'BY': '🇧🇾'  
    }  
    return flag_map.get(country_code, '🌍')  

def get_bin_info(cc):  
    result = {  
        'brand': 'Unknown',  
        'type': 'Unknown',  
        'level': 'Unknown',  
        'bank': 'Unknown',  
        'country': 'Unknown',  
        'flag': '🌍'  
    }  
      
    try:  
        response = requests.get(f"https://lookup.binlist.net/{cc[:6]}",   
                                headers={'Accept-Version': '3'},  
                                timeout=8)  
        if response.status_code == 200:  
            data = response.json()  
            result['brand'] = data.get('scheme', 'Unknown').upper()  
            result['type'] = data.get('type', 'Unknown').upper()  
            result['level'] = data.get('brand', 'Unknown').upper()  
            result['bank'] = data.get('bank', {}).get('name', 'Unknown')  
            result['country'] = data.get('country', {}).get('name', 'Unknown')  
            country_code = data.get('country', {}).get('alpha2', '')  
            result['flag'] = get_country_flag(country_code)  
            return result  
    except:  
        pass  
      
    try:  
        data_bin = requests.get('https://bins.antipublic.cc/bins/'+cc[:6], timeout=5).json()  
        result['bank'] = data_bin.get('bank', 'Unknown')  
        result['country'] = data_bin.get('country_name', 'Unknown')  
        result['flag'] = data_bin.get('country_flag', '🌍')  
        result['brand'] = data_bin.get('brand', 'Unknown')  
        result['type'] = data_bin.get('type', 'Unknown')  
        result['level'] = data_bin.get('level', 'Standard')  
        return result  
    except:  
        pass  
      
    return result  

def format_bin_info(bin_data):  
    return f"""[ϟ] <b>Info: {bin_data['brand']} · {bin_data['type']} · {bin_data['level']}</b>  
[ϟ] <b>Bank: {bin_data['bank']}</b>  
[ϟ] <b>Country: {bin_data['country']} {bin_data['flag']}</b>"""  

@bot.message_handler(commands=['bin'])  
def bin_lookup_command(message):  
    try:  
        args = message.text.split()  
        if len(args) < 2:  
            bot.reply_to(message, "<b>❌ Please provide a BIN number!\nUsage: /bin 123456</b>", parse_mode="HTML")  
            return  
          
        bin_num = args[1].strip()  
        if len(bin_num) < 6:  
            bot.reply_to(message, "<b>❌ BIN must be at least 6 digits!</b>", parse_mode="HTML")  
            return  
          
        wait_msg = bot.reply_to(message, "<b>⏳ Looking up BIN...</b>", parse_mode="HTML")  
        bin_data = get_bin_info(bin_num)  
          
        result_msg = f"""<b>🔍 BIN Lookup Result</b>  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] <b>BIN:</b> <code>{bin_num}</code>  
[ϟ] <b>Brand:</b> {bin_data['brand']}  
[ϟ] <b>Type:</b> {bin_data['type']}  
[ϟ] <b>Level:</b> {bin_data['level']}  
[ϟ] <b>Bank:</b> {bin_data['bank']}  
[ϟ] <b>Country:</b> {bin_data['country']} {bin_data['flag']}  
- - - - - - - - - - - - - - - - - - - - - -  
[⌤] <b>Dev by: {OWNER_NAME} - @{OWNER_USERNAME} 🗣</b>"""  
          
        bot.delete_message(message.chat.id, wait_msg.message_id)  
        bot.send_message(message.chat.id, result_msg, parse_mode="HTML")  
          
    except Exception as e:  
        bot.reply_to(message, f"<b>❌ Error: {str(e)}</b>", parse_mode="HTML")  

# ============================================  
# Card Extraction & Combo Functions  
# ============================================  

def extract_card_from_line(line):  
    line = line.strip()  
    card_pattern = r'(\d{13,19})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})'  
    match = re.search(card_pattern, line)  
      
    if match:  
        pan = match.group(1)  
        month = match.group(2).zfill(2)  
        year = match.group(3)  
        cvv = match.group(4)  
          
        if len(year) == 4:  
            year = year[2:]  
          
        return f"{pan}|{month}|{year}|{cvv}"  
      
    return None  

def clean_combo(cards):  
    cleaned = []  
    seen = set()  
      
    for card in cards:  
        extracted = extract_card_from_line(card)  
        if not extracted:  
            continue  
          
        parts = extracted.split('|')  
        if len(parts) != 4:  
            continue  
          
        pan = parts[0]  
        month = parts[1]  
        year = parts[2]  
        cvv = parts[3]  
          
        try:  
            current_year = datetime.now().year % 100  
            current_month = datetime.now().month  
            card_year = int(year)  
            card_month = int(month)  
              
            if card_year < current_year or (card_year == current_year and card_month < current_month):  
                continue  
        except:  
            pass  
          
        if not pan.isdigit() or len(pan) < 13 or len(pan) > 19:  
            continue  
        if not month.isdigit() or int(month) < 1 or int(month) > 12:  
            continue  
        if not year.isdigit() or len(year) not in [2, 4]:  
            continue  
        if not cvv.isdigit() or len(cvv) not in [3, 4]:  
            continue  
          
        normalized = f"{pan}|{month}|{year}|{cvv}"  
        if normalized not in seen:  
            seen.add(normalized)  
            cleaned.append(normalized)  
      
    return cleaned  

def shuffle_combo(cards):  
    shuffled = cards.copy()  
    random.shuffle(shuffled)  
    return shuffled  

# ============================================  
# Send to Channels Functions (Disabled)  
# ============================================  

def send_to_full_channel(card, result, status, bin_info, user_name, gateway_name, is_charged=True):  
    if not CHANNEL_FULL:
        return
    try:  
        clean_user_name = re.sub(r'<[^>]+>', '', str(user_name))  
        if is_charged:  
            channel_msg = f"""<b>#{gateway_name} 🔥 CHARGED</b>  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] Card: <code>{card}</code>  
[ϟ] Response: {result}  
[ϟ] Status: {status}  
- - - - - - - - - - - - - - - - - - - - - -  
{bin_info}  
- - - - - - - - - - - - - - - - - - - - - -  
[⎇] Checked by: {clean_user_name}  
- - - - - - - - - - - - - - - - - - - - - -  
[⌤] Dev by: {OWNER_NAME} - @{OWNER_USERNAME} 🗣"""  
        else:  
            channel_msg = f"""<b>#{gateway_name} ✅ APPROVED</b>  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] Card: <code>{card}</code>  
[ϟ] Response: {result}  
[ϟ] Status: {status}  
- - - - - - - - - - - - - - - - - - - - - -  
{bin_info}  
- - - - - - - - - - - - - - - - - - - - - -  
[⎇] Checked by: {clean_user_name}  
- - - - - - - - - - - - - - - - - - - - - -  
[⌤] Dev by: {OWNER_NAME} - @{OWNER_USERNAME} 🗣"""  
        bot.send_message(CHANNEL_FULL, channel_msg, parse_mode="HTML")  
    except Exception as e:  
        print(f"Error sending to full channel: {e}")  

def send_to_hits_channel(user_name, status, response, gateway_name):  
    if not CHANNEL_HITS:
        return
    try:  
        clean_user_name = re.sub(r'<[^>]+>', '', str(user_name))  
        status_display = "Charged 🔥" if "Charge" in status else "Approved ✅"  
        response_display = "Charge 🔥" if "Charge" in response else f"{response} ✅"  
        channel_msg = f"""[ϟ] 𝗛𝗶𝘁 𝗗𝗲𝘁𝗲𝗰𝘁𝗲𝗱  🔥  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] 𝐔𝐬𝐞𝐫: {clean_user_name} • [𝗩𝗜𝗣]  
[ϟ] 𝐒𝐭𝐚𝐭𝐮𝐬: {status_display}  
[ϟ] 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {response_display}  
[ϟ] 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: {gateway_name}  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] @{OWNER_USERNAME}"""  
        bot.send_message(CHANNEL_HITS, channel_msg, parse_mode="HTML")  
    except Exception as e:  
        print(f"Error sending to hits channel: {e}")  

# ============================================  
# Combo Check Thread  
# ============================================  

def combo_check_thread(user_id, chat_id, message_id, total_cards, username):  
    try:  
        session = users_checking_files.get(user_id)  
        if not session:  
            return  
        
        cards = session['cards']  
        gateway_display = "PayPal_Donation ($5.00)"  
        gateway_func = PayPal_1  
        
        checked = 0  
        charged = 0  
        approved = 0  
        declined = 0  
        
        session['charged'] = []
        session['approved'] = []
        session['declined'] = []
        
        # Create progress message with buttons
        progress_markup = types.InlineKeyboardMarkup(row_width=2)
        progress_markup.add(
            types.InlineKeyboardButton("⏹️ Stop", callback_data="combo_stop"),
            types.InlineKeyboardButton("📊 Stats", callback_data="combo_stats")
        )
        
        progress_text = f"""<b>📁 Combo Check Running</b>
━━━━━━━━━━━━━━━━━━━━━━
[ϟ] <b>Gateway:</b> {gateway_display}
[ϟ] <b>By:</b> @{username}
━━━━━━━━━━━━━━━━━━━━━━
<b>📊 Progress:</b>
├ 🔥 Charged: 0
├ ✅ Approved: 0
└ ❌ Declined: 0
━━━━━━━━━━━━━━━━━━━━━━
<b>📈 Cards:</b> 0/{total_cards} (0%)
━━━━━━━━━━━━━━━━━━━━━━
[⌤] <b>Dev by: {OWNER_NAME} - @{OWNER_USERNAME} 🗣</b>"""
        
        bot.edit_message_text(progress_text, chat_id, message_id, parse_mode="HTML", reply_markup=progress_markup)
        
        for index, card in enumerate(cards):  
            if stopuser.get(user_id, False):  
                break  
            
            bin_data = get_bin_info(card)  
            bin_info = format_bin_info(bin_data)  
            
            try:  
                result = gateway_func(card)  
            except Exception as e:  
                result = f"Error: {str(e)}"  
            
            checked += 1  
            percentage = int((checked / total_cards) * 100)
            display_name = f"@{username}" if username != "NoUsername" else session.get('first_name', 'User')  
            
            send_result = False
            result_status = ""
            
            res_up = str(result).upper()
            if any(x in res_up for x in ['CHARGED', 'COMPLETED', 'SUCCESS', 'CAPTURED']):
                charged += 1  
                session['charged'].append(card)  
                result_status = "CHARGED"
                send_result = True
                send_to_full_channel(card, result, "Charged $", bin_info, display_name, gateway_display, is_charged=True)  
                send_to_hits_channel(display_name, "Charged 🔥", result, gateway_display)  
            elif any(x in res_up for x in ['INSUFFICIENT_FUNDS', 'INSUFFICIENT FUNDS', 'NOT_SUFFICIENT_FUNDS']):
                approved += 1  
                session['approved'].append(card)  
                result_status = "APPROVED (Insufficient Funds)"
                send_result = True
                send_to_full_channel(card, result, "Approved ✅", bin_info, display_name, gateway_display, is_charged=False)  
                send_to_hits_channel(display_name, "Approved ✅", result, gateway_display)  
            else:
                declined += 1  
                session['declined'].append(card)  
                result_status = "DECLINED"
                send_result = False
                session['declined'].append(card)  
                result_status = "DECLINED"
                send_result = False
            
            if send_result:
                result_msg = f"""<b>#{gateway_display} - {result_status}</b>
- - - - - - - - - - - - - - - - - - - - - -
[ϟ] <b>Card:</b> <code>{card}</code>
[ϟ] <b>Response:</b> {result}
- - - - - - - - - - - - - - - - - - - - - -
{bin_info}
- - - - - - - - - - - - - - - - - - - - - -
[⎇] <b>Checked by:</b> {display_name}
- - - - - - - - - - - - - - - - - - - - - -
[⌤] <b>Dev by: {OWNER_NAME} - @{OWNER_USERNAME} 🗣</b>"""
                bot.send_message(chat_id, result_msg, parse_mode="HTML")
            
            # Update progress
            progress_markup = types.InlineKeyboardMarkup(row_width=2)
            progress_markup.add(
                types.InlineKeyboardButton("⏹️ Stop", callback_data="combo_stop"),
                types.InlineKeyboardButton("📊 Stats", callback_data="combo_stats")
            )
            
            progress_text = f"""<b>📁 Combo Check Running</b>
━━━━━━━━━━━━━━━━━━━━━━
[ϟ] <b>Gateway:</b> {gateway_display}
[ϟ] <b>By:</b> @{username}
━━━━━━━━━━━━━━━━━━━━━━
<b>📊 Progress:</b>
├ 🔥 Charged: {charged}
├ ✅ Approved: {approved}
└ ❌ Declined: {declined}
━━━━━━━━━━━━━━━━━━━━━━
<b>📈 Cards:</b> {checked}/{total_cards} ({percentage}%)
━━━━━━━━━━━━━━━━━━━━━━
[⌤] <b>Dev by: {OWNER_NAME} - @{OWNER_USERNAME} 🗣</b>"""
            
            try:
                bot.edit_message_text(progress_text, chat_id, message_id, parse_mode="HTML", reply_markup=progress_markup)
            except:
                pass
            
            time.sleep(1.5)  
        
        session['running'] = False  
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        if session['charged']:
            markup.add(types.InlineKeyboardButton(f"🔥 Charged ({len(session['charged'])})", callback_data="get_charged"))
        if session['approved']:
            markup.add(types.InlineKeyboardButton(f"✅ Approved ({len(session['approved'])})", callback_data="get_approved"))
        if session['declined']:
            markup.add(types.InlineKeyboardButton(f"❌ Declined ({len(session['declined'])})", callback_data="get_declined"))
        
        final_text = f"""<b>✅ Combo Check Complete!</b>
━━━━━━━━━━━━━━━━━━━━━━
[ϟ] <b>Gateway:</b> {gateway_display}
[ϟ] <b>Total Cards:</b> {total_cards}
━━━━━━━━━━━━━━━━━━━━━━
<b>📊 Final Results:</b>
├ 🔥 Charged: {charged}
├ ✅ Approved: {approved}
└ ❌ Declined: {declined}
━━━━━━━━━━━━━━━━━━━━━━
[⌤] <b>Dev by: {OWNER_NAME} - @{OWNER_USERNAME} 🗣</b>"""
        
        bot.edit_message_text(final_text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
        
    except Exception as e:
        bot.send_message(chat_id, f"<b>❌ Error in check: {str(e)}</b>", parse_mode="HTML")

# ============================================  
# Admin Commands  
# ============================================  

@bot.message_handler(commands=['addtime'])  
def add_time_command(message):  
    if not is_owner(message.from_user.id):  
        bot.reply_to(message, "⛔ Admin only!")  
        return  
      
    try:  
        args = message.text.split()  
        if len(args) < 3:  
            bot.reply_to(message, "⚠️ Usage: /addtime user_id hours\nExample: /addtime 123456789 24")  
            return  
          
        user_id = int(args[1])  
        hours = int(args[2])  
          
        new_expiry = add_subscription_time(user_id, hours)  
        remaining = new_expiry - time.time()  
        hours_remaining = int(remaining // 3600)  
        mins_remaining = int((remaining % 3600) // 60)  
          
        bot.reply_to(message, f"✅ Added {hours} hours to user {user_id}\n⏰ Remaining: {hours_remaining}h {mins_remaining}m")  
          
        try:  
            bot.send_message(user_id, f"🎉 {hours} hours added to your subscription!\n⏰ Expires in: {hours_remaining}h {mins_remaining}m")  
        except:  
            pass  
              
    except Exception as e:  
        bot.reply_to(message, f"❌ Error: {e}")  

@bot.message_handler(commands=['addpoints'])  
def add_points_command(message):  
    if not is_owner(message.from_user.id):  
        bot.reply_to(message, "⛔ Admin only!")  
        return  
      
    try:  
        args = message.text.split()  
        if len(args) < 3:  
            bot.reply_to(message, "⚠️ Usage: /addpoints user_id points\nExample: /addpoints 123456789 50")  
            return  
          
        user_id = args[1]  
        points = int(args[2])  
          
        new_balance = add_points(user_id, points)  
        bot.reply_to(message, f"✅ Added {points} points to user {user_id}\n💰 New balance: {new_balance} points")  
          
        try:  
            bot.send_message(user_id, f"🎉 {points} points added to your balance!\n💰 Your balance: {new_balance} points")  
        except:  
            pass  
              
    except Exception as e:  
        bot.reply_to(message, f"❌ Error: {e}")  

@bot.message_handler(commands=['users'])  
def list_users_command(message):  
    if not is_owner(message.from_user.id):  
        bot.reply_to(message, "⛔ Admin only!")  
        return  
      
    data = read_data()  
    if not data:  
        bot.reply_to(message, "📭 No users found")  
        return  
      
    text = "📊 <b>Users List</b>\n━━━━━━━━━━━━━━━━\n"  
    for user_id, user_data in list(data.items())[:20]:  
        points = user_data.get('points', 0)  
        sub_end = max(user_data.get('subscription_end', 0), user_data.get('subscription_expiry', 0))  
        if sub_end > time.time():  
            remaining = sub_end - time.time()  
            hours = int(remaining // 3600)  
            text += f"👤 <code>{user_id}</code> - Active ({hours}h) | 💰 {points} points\n"  
        elif points > 0:  
            text += f"👤 <code>{user_id}</code> - {points} points\n"  
        else:  
            text += f"👤 <code>{user_id}</code> - Inactive\n"  
      
    if len(data) > 20:  
        text += f"\n... and {len(data) - 20} more users"  
      
    bot.reply_to(message, text, parse_mode="HTML")  

@bot.message_handler(commands=['deluser'])  
def delete_user_command(message):  
    if not is_owner(message.from_user.id):  
        bot.reply_to(message, "⛔ Admin only!")  
        return  
      
    try:  
        args = message.text.split()  
        if len(args) < 2:  
            bot.reply_to(message, "⚠️ Usage: /deluser user_id")  
            return  
          
        user_id = args[1]  
        data = read_data()  
          
        if user_id in data:  
            del data[user_id]  
            write_data(data)  
            bot.reply_to(message, f"✅ Deleted user {user_id}")  
        else:  
            bot.reply_to(message, f"❌ User {user_id} not found")  
              
    except Exception as e:  
        bot.reply_to(message, f"❌ Error: {e}")  

# ============================================  
# User Commands  
# ============================================  

@bot.message_handler(commands=['start'])  
def start_handler(message):  
    user_id = message.from_user.id  
    first_name = message.from_user.first_name or "User"  
    username = message.from_user.username or "NoUsername"  
      
    ensure_user(user_id, first_name, username)  
    sub_status = get_remaining_time(user_id)  
      
    inline_markup = types.InlineKeyboardMarkup(row_width=2)  
    inline_markup.add(  
        types.InlineKeyboardButton("📋 Commands", callback_data="commands"),  
        types.InlineKeyboardButton("ℹ️ Info", callback_data="info"),  
        types.InlineKeyboardButton("⭐ Subscribe", callback_data="subscribe"),  
        types.InlineKeyboardButton("🔍 BIN Lookup", callback_data="bin_lookup"),  
        types.InlineKeyboardButton("💰 My Balance", callback_data="my_balance"),  
        types.InlineKeyboardButton("👨‍💻 Owner", callback_data="owner_info")  
    )  
      
    reply_markup = get_main_keyboard()  
      
    text = f"""<b>  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] Welcome to PayPal Donation Checker 🔥  
- - - - - - - - - - - - - - - - - - - - - -  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] Hello, {first_name}!  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] Gateway: PayPal Donation ($5.00)  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] Balance: {sub_status}  
- - - - - - - - - - - - - - - - - - - - - -  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] Use /pp to check a card (0.5 points)  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] Use /bin to look up BIN  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] Upload .txt file for combo check  
- - - - - - - - - - - - - - - - - - - - - -  
[<a href="https://t.me/{OWNER_USERNAME}">⌤</a>] Dev by: {OWNER_NAME} - @{OWNER_USERNAME} 🗣  
</b>"""  
      
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=reply_markup)  
    bot.send_message(message.chat.id, "<b>🔽 Choose from the buttons below:</b>", parse_mode="HTML", reply_markup=inline_markup)  

@bot.message_handler(commands=['mypoints'])  
def my_points_command(message):  
    user_id = message.from_user.id  
    sub_status = get_remaining_time(user_id)  
    ensure_user(user_id, message.from_user.first_name or "User", message.from_user.username or "NoUsername")  
      
    data = read_data()  
    uid = str(user_id)  
    points = data.get(uid, {}).get('points', 0)  
      
    if has_subscription(user_id):  
        text = f"⭐ <b>Your Balance</b>\n━━━━━━━━━━━━━━━━\n💰 <b>Points:</b> {points}\n⏰ <b>Subscription:</b> {sub_status}\n\n💡 Use /pp to check cards (costs 0.5 points)\n💡 Upload .txt file for combo check"  
    else:  
        text = f"⭐ <b>Your Balance</b>\n━━━━━━━━━━━━━━━━\n💰 <b>Points:</b> {points}\n❌ <b>Status:</b> No active subscription\n\nUse /subscribe to buy stars plan\nor use points (0.5 per check)\n\n💡 Use /pp to check cards"  
      
    bot.reply_to(message, text, parse_mode="HTML")  

@bot.message_handler(commands=['help'])  
def help_command(message):  
    help_text = f"""<b>🤖 PayPal Donation Bot - Help</b>  
━━━━━━━━━━━━━━━━━━━━━━  
  
<b>📋 Available Commands:</b>  
/start - Start the bot  
/pp [card] - Check single card (0.5 points)  
/bin [bin] - Look up BIN information  
/myamount - Set your check amount  
/mypoints - Check your balance  
/subscribe - Buy subscription with stars  
/status - Check subscription status  
/help - Show this help menu  
  
<b>📁 File Check:</b>  
Send a .txt file with cards (one per line)  
Format: card|month|year|cvv  
Max cards: {MAX_CARDS} per file  
  
<b>🧹 File Tools:</b>  
After uploading a file, you can:  
• Clean - Remove duplicates and expired cards  
• Shuffle - Randomize card order  
• Start Check - Begin checking cards  
  
<b>💳 Card Format:</b>  
<code>1234567890123456|12|25|123</code>  
  
<b>💰 Gateway:</b>  
• #PayPal_Donation ($5.00)  
  
<b>👨‍💻 Developer:</b> @{OWNER_USERNAME}  
  
━━━━━━━━━━━━━━━━━━━━━━  
<i>Send /pp to check a card</i>"""  
      
    bot.reply_to(message, help_text, parse_mode="HTML")  

@bot.message_handler(commands=['status'])  
def status_command(message):  
    user_id = message.from_user.id  
    sub_status = get_remaining_time(user_id)  
      
    data = read_data()  
    uid = str(user_id)  
    points = data.get(uid, {}).get('points', 0)  
      
    if has_subscription(user_id):  
        text = f"⭐ <b>Subscription Status</b>\n━━━━━━━━━━━━━━━━\n✅ <b>Active</b>\n💰 <b>Points:</b> {points}\n⏰ <b>Remaining:</b> {sub_status}\n\n💵 <b>Gateway:</b> PayPal $5.00"  
    else:  
        text = f"⭐ <b>Subscription Status</b>\n━━━━━━━━━━━━━━━━\n❌ <b>No active subscription</b>\n💰 <b>Points:</b> {points}\n\nUse /subscribe to buy stars plan\nor use points (0.5 per check)\n\n💵 <b>Gateway:</b> PayPal $5.00"  
      
    bot.reply_to(message, text, parse_mode="HTML")  

@bot.message_handler(commands=['myamount'])  
def set_amount_command(message):  
    bot.reply_to(  
        message,  
        f"<b>💰 Gateway: #PayPal_Donation ($5.00)</b>\n\n<i>Amount is fixed at $5.00</i>",  
        parse_mode="HTML"  
    )  

# ============================================  
# Telegram Stars Payment Handling  
# ============================================  

@bot.message_handler(commands=['subscribe'])  
def subscribe_command(message):  
    chat_id = message.chat.id  
    user_id = message.from_user.id  
    sub_status = get_remaining_time(user_id)  
      
    markup = types.InlineKeyboardMarkup(row_width=1)  
    markup.add(  
        types.InlineKeyboardButton("⏰ 1 Hour (15⭐)", callback_data="sub_1h"),  
        types.InlineKeyboardButton("⏰ 24 Hours (70⭐)", callback_data="sub_24h"),  
        types.InlineKeyboardButton("🔙 Back", callback_data="back_main")  
    )  
      
    text = f"""<b>  
[ϟ] Buy Subscription ⏰  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] Current Status: {sub_status}  
- - - - - - - - - - - - - - - - - - - - - -  
⏰ Hourly Subscriptions (Unlimited Checks):  
[ϟ] 1 Hour = 15⭐  
[ϟ] 24 Hours = 70⭐  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] Pay with Telegram Stars ⭐  
</b>"""  
      
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)  

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))  
def handle_subscription(call):  
    package = call.data.split('_')[1]  
      
    packages = {  
        '1h': {'hours': 1, 'stars': 15, 'title': '1 Hour Subscription', 'description': 'Unlimited checks for 1 hour'},  
        '24h': {'hours': 24, 'stars': 70, 'title': '24 Hours Subscription', 'description': 'Unlimited checks for 24 hours'}  
    }  
      
    if package not in packages:  
        return  
      
    pkg = packages[package]  
    hours = pkg['hours']  
    stars = pkg['stars']  
      
    prices = [types.LabeledPrice(label=f"{hours} Hours", amount=stars)]  
      
    bot.send_invoice(  
        chat_id=call.message.chat.id,  
        title=pkg['title'],  
        description=pkg['description'],  
        invoice_payload=f"sub_{package}_{call.from_user.id}",  
        provider_token="",  
        currency="XTR",  
        prices=prices  
    )  

@bot.pre_checkout_query_handler(func=lambda query: True)  
def checkout_handler(pre_checkout_query):  
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)  

@bot.message_handler(content_types=["successful_payment"])  
def successful_payment(message):  
    payload = message.successful_payment.invoice_payload  
    parts = payload.split('_')  
    package = parts[1]  
    user_id = int(parts[2])  
      
    packages = {  
        '1h': {'hours': 1, 'stars': 15},  
        '24h': {'hours': 24, 'stars': 70}  
    }  
      
    if package not in packages:  
        return  
      
    hours = packages[package]['hours']  
    stars = packages[package]['stars']  
      
    new_expiry = add_subscription_time(user_id, hours)  
    remaining = new_expiry - time.time()  
    hours_remaining = int(remaining // 3600)  
    mins_remaining = int((remaining % 3600) // 60)  
      
    success_msg = f"""<b>  
[ϟ] Payment Successful ✅  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] Subscribed for {hours} Hour(s) ⏰  
[ϟ] Remaining: {hours_remaining}h {mins_remaining}m  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] Thank You For Your Purchase! 🌟  
</b>"""  
    bot.send_message(message.chat.id, success_msg, parse_mode="HTML")  
      
    try:  
        username = message.from_user.username or "No Username"  
        first_name = message.from_user.first_name or "User"  
          
        owner_msg = f"""<b>💰 New Payment!  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] User: {first_name} (@{username})  
[ϟ] ID: <code>{user_id}</code>  
[ϟ] Package: {hours} Hour(s)  
[ϟ] Amount: {stars} ⭐  
- - - - - - - - - - - - - - - - - - - - - -  
</b>"""  
        bot.send_message(OWNER_ID, owner_msg, parse_mode="HTML")  
    except:  
        pass  

# ============================================  
# File Handler - Combo Check  
# ============================================  

@bot.message_handler(content_types=['document'])  
def document_handler(message):  
    user_id = message.from_user.id  
      
    if user_id != OWNER_ID:  
        data = read_data()  
        uid = str(user_id)  
        points = data.get(uid, {}).get('points', 0)  
        has_sub = has_subscription(user_id)  
          
        if not has_sub and points < 0.5:  
            markup = types.InlineKeyboardMarkup()  
            markup.add(types.InlineKeyboardButton("⭐ Subscribe Now", callback_data="subscribe"))  
            bot.reply_to(  
                message,  
                f"⚠️ <b>Insufficient Balance!</b>\n\n"  
                f"You need an active subscription or points to check files.\n\n"  
                f"💰 <b>Your points:</b> {points}\n"  
                f"💳 <b>Check cost:</b> 0.5 points per card\n\n"  
                f"Click the button below to subscribe!",  
                parse_mode="HTML",  
                reply_markup=markup  
            )  
            return  
      
    first_name = message.from_user.first_name or "User"  
    username = message.from_user.username or "NoUsername"  
      
    if not message.document.file_name.endswith('.txt'):  
        bot.reply_to(message, "<b>❌ Please upload a .txt file</b>", parse_mode="HTML")  
        return  
      
    if user_id in users_checking_files and users_checking_files[user_id].get('running'):  
        bot.reply_to(message, "<b>❌ You already have an active session!</b>", parse_mode="HTML")  
        return  
      
    try:  
        file_info = bot.get_file(message.document.file_id)  
        downloaded_file = bot.download_file(file_info.file_path)  
        content = downloaded_file.decode('utf-8', errors='ignore')  
          
        lines = [l.strip() for l in content.split('\n') if l.strip()]  
        cards = []  
          
        for line in lines:  
            extracted = extract_card_from_line(line)  
            if extracted:  
                cards.append(extracted)  
          
        if not cards:  
            bot.reply_to(message, "<b>❌ No valid cards found in file!</b>", parse_mode="HTML")  
            return  
          
        if len(cards) > MAX_CARDS:  
            bot.reply_to(message, f"<b>❌ File has {len(cards)} cards. Maximum is {MAX_CARDS}</b>", parse_mode="HTML")  
            return  
          
        cleaned_cards = clean_combo(cards)  
          
        users_checking_files[user_id] = {  
            'cards': cleaned_cards,  
            'running': False,  
            'username': username,  
            'first_name': first_name,  
            'original_count': len(cards),  
            'charged': [],  
            'approved': [],  
            'declined': [],  
            'gateway': 'PayPal_1'  
        }  
          
        # Show control menu directly (no gateway selection needed)
        markup = types.InlineKeyboardMarkup(row_width=2)  
        markup.add(  
            types.InlineKeyboardButton("🧹 Clean", callback_data="combo_clean"),  
            types.InlineKeyboardButton("🔀 Shuffle", callback_data="combo_shuffle"),  
            types.InlineKeyboardButton("▶️ START", callback_data="combo_start")  
        )  
          
        text = f"""<b>Gateway: #PayPal_Donation ($5.00)  
By: @{username}  
📁 Cards: {len(cleaned_cards)} / {len(cards)}</b>"""  
          
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)  
          
    except Exception as e:  
        bot.reply_to(message, f"<b>❌ Error reading file: {str(e)}</b>", parse_mode="HTML")  

# ============================================  
# PP Command - Manual Check  
# ============================================  

@bot.message_handler(commands=['pp'])  
def pp_command(message):  
    try:  
        user_id = message.from_user.id  
        username = message.from_user.username or "No Username"  
        first_name = message.from_user.first_name or "User"  
          
        ensure_user(user_id, first_name, username)  
          
        cc = None  
        try:  
            parts = message.text.split(None, 1)  
            if len(parts) > 1:  
                cc = parts[1].strip()  
        except:  
            pass  
          
        if not cc and message.reply_to_message:  
            try:  
                reply_text = message.reply_to_message.text or ""  
                card_pattern = r'\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}'  
                match = re.search(card_pattern, reply_text)  
                if match:  
                    cc = match.group(0)  
            except:  
                pass  
          
        if not cc:  
            bot.reply_to(message, "<b>❌ Please use format:\n/pp card|month|year|cvv</b>", parse_mode="HTML")  
            return  
          
        if '|' not in cc or len(cc.split('|')) != 4:  
            bot.reply_to(message, "<b>❌ Invalid card format!\nUse: /pp card|month|year|cvv</b>", parse_mode="HTML")  
            return  
        
        if user_id != OWNER_ID:  
            data = read_data()  
            uid = str(user_id)  
            points = data.get(uid, {}).get('points', 0)  
            has_sub = has_subscription(user_id)  
              
            if not has_sub and points < 0.5:  
                markup = types.InlineKeyboardMarkup()  
                markup.add(types.InlineKeyboardButton("⭐ Subscribe Now", callback_data="subscribe"))  
                bot.reply_to(  
                    message,  
                    f"⚠️ <b>Insufficient Balance!</b>\n\n"  
                    f"You don't have an active subscription or enough points.\n\n"  
                    f"💰 <b>Your points:</b> {points}\n"  
                    f"💳 <b>Check cost:</b> 0.5 points\n\n"  
                    f"Click the button below to subscribe!",  
                    parse_mode="HTML",  
                    reply_markup=markup  
                )  
                return  
          
        # Show loading message
        wait_msg = bot.reply_to(message, "<b>⏳ Checking your card...</b>", parse_mode="HTML")
        
        bin_data = get_bin_info(cc)  
        bin_info = format_bin_info(bin_data)  
        
        start_time = time.time()  
        
        try:  
            result = PayPal_1(cc)  
        except Exception as e:  
            result = f"Error: {str(e)}"  
        
        end_time = time.time()  
        execution_time = end_time - start_time  
        
        data = read_data()  
        uid = str(user_id)  
        if uid in data:  
            data[uid]['total_checks'] = data[uid].get('total_checks', 0) + 1  
            write_data(data)  
        
        display_name = f"@{username}" if username != "No Username" else first_name  
        
        data = read_data()  
        points_left = data.get(uid, {}).get('points', 0)  
        
        res_up = str(result).upper()
        if any(x in res_up for x in ['CHARGED', 'COMPLETED', 'SUCCESS', 'CAPTURED']):
            status_text = result
            response_text = result
            result_status = "CHARGED"
            send_to_full_channel(cc, result, "Charged $", bin_info, display_name, "PayPal_Donation ($5.00)", is_charged=True)  
            send_to_hits_channel(display_name, "Charged 🔥", result, "PayPal_Donation ($5.00)")  
        elif any(x in res_up for x in ['INSUFFICIENT_FUNDS', 'INSUFFICIENT FUNDS', 'NOT_SUFFICIENT_FUNDS']):
            status_text = result
            response_text = result
            result_status = "APPROVED"
            send_to_full_channel(cc, result, "Approved ✅", bin_info, display_name, "PayPal_Donation ($5.00)", is_charged=False)  
            send_to_hits_channel(display_name, "Approved ✅", result, "PayPal_Donation ($5.00)")  
        else:  
            status_text = result
            response_text = result
            result_status = "DECLINED"
        
        points_info = ""
        if user_id != OWNER_ID:
            points_info = f"\n[ϟ] <b>Points left:</b> {points_left}"
        
        result_msg = f"""<b>#PayPal_Donation ($5.00) - {result_status}</b>  
- - - - - - - - - - - - - - - - - - - - - -  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] <b>Card:</b> <code>{cc}</code>  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] <b>Response:</b> {response_text}  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] <b>Status:</b> {status_text}  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] <b>Taken:</b> {execution_time:.1f} S.  
- - - - - - - - - - - - - - - - - - - - - -  
{bin_info}{points_info}  
- - - - - - - - - - - - - - - - - - - - - -  
[<a href="https://t.me/{OWNER_USERNAME}">⎇</a>] <b>Req By:</b> {display_name}  
- - - - - - - - - - - - - - - - - - - - - -  
[<a href="https://t.me/{OWNER_USERNAME}">⌤</a>] <b>Dev by: {OWNER_NAME} - @{OWNER_USERNAME} 🗣</b>"""  
        
        bot.delete_message(message.chat.id, wait_msg.message_id)  
        bot.send_message(message.chat.id, result_msg, parse_mode="HTML")
          
    except Exception as e:  
        bot.reply_to(message, f"<b>❌ Error: {str(e)}</b>", parse_mode="HTML")

# ============================================  
# Callback Handler  
# ============================================  

@bot.callback_query_handler(func=lambda call: True)  
def callback_handler(call):  
    chat_id = call.message.chat.id  
    user_id = call.from_user.id  
    
    # ========== STATS BUTTON ==========
    if call.data == "combo_stats":
        if user_id not in users_checking_files:
            bot.answer_callback_query(call.id, "❌ No active session")
            return
        
        session = users_checking_files[user_id]
        if not session.get('running'):
            bot.answer_callback_query(call.id, "❌ No active check running")
            return
        
        total = len(session['cards'])
        checked = len(session['charged']) + len(session['approved']) + len(session['declined'])
        charged = len(session['charged'])
        approved = len(session['approved'])
        declined = len(session['declined'])
        remaining = total - checked
        
        stats_text = f"""<b>📊 Live Statistics</b>
━━━━━━━━━━━━━━━━━━━━━━
[ϟ] <b>Total Cards:</b> {total}
[ϟ] <b>Checked:</b> {checked}
[ϟ] <b>Remaining:</b> {remaining}
━━━━━━━━━━━━━━━━━━━━━━
🔥 <b>Charged:</b> {charged}
✅ <b>Approved:</b> {approved}
❌ <b>Declined:</b> {declined}
━━━━━━━━━━━━━━━━━━━━━━
<b>📈 Progress:</b> {int((checked/total)*100) if total > 0 else 0}%"""
        
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, stats_text, parse_mode="HTML")
    
    # ========== COMBO ACTIONS ==========
    elif call.data == "combo_start":  
        if user_id not in users_checking_files:  
            bot.answer_callback_query(call.id, "❌ No combo loaded")  
            return  
          
        session = users_checking_files[user_id]  
        if session.get('running'):  
            bot.answer_callback_query(call.id, "⚠️ Already running")  
            return  
          
        session['running'] = True  
        stopuser[user_id] = False  
        bot.answer_callback_query(call.id, "▶️ Starting...")  
        
        # Add control buttons
        control_markup = types.InlineKeyboardMarkup(row_width=2)
        control_markup.add(
            types.InlineKeyboardButton("⏹️ Stop", callback_data="combo_stop"),
            types.InlineKeyboardButton("📊 Stats", callback_data="combo_stats")
        )
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=control_markup)
          
        threading.Thread(target=combo_check_thread, args=(user_id, chat_id, call.message.message_id, len(session['cards']), session['username'])).start()  
      
    elif call.data == "combo_clean":  
        if user_id not in users_checking_files:  
            bot.answer_callback_query(call.id, "❌ No combo loaded")  
            return  
          
        session = users_checking_files[user_id]  
        original_count = len(session['cards'])  
        cleaned = clean_combo(session['cards'])  
        session['cards'] = cleaned  
          
        bot.answer_callback_query(call.id, f"🧹 Cleaned: {original_count} → {len(cleaned)} cards")  
          
        markup = types.InlineKeyboardMarkup(row_width=2)  
        markup.add(  
            types.InlineKeyboardButton("🧹 Clean", callback_data="combo_clean"),  
            types.InlineKeyboardButton("🔀 Shuffle", callback_data="combo_shuffle"),  
            types.InlineKeyboardButton("▶️ START", callback_data="combo_start")  
        )  
          
        text = f"""<b>Gateway: #PayPal_Donation ($5.00)  
By: @{session['username']}  
📁 Cards: {len(cleaned)} (cleaned from {original_count})</b>"""  
          
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)  
      
    elif call.data == "combo_shuffle":  
        if user_id not in users_checking_files:  
            bot.answer_callback_query(call.id, "❌ No combo loaded")  
            return  
          
        session = users_checking_files[user_id]  
        session['cards'] = shuffle_combo(session['cards'])  
          
        bot.answer_callback_query(call.id, "🔀 Cards shuffled!")  
          
        markup = types.InlineKeyboardMarkup(row_width=2)  
        markup.add(  
            types.InlineKeyboardButton("🧹 Clean", callback_data="combo_clean"),  
            types.InlineKeyboardButton("🔀 Shuffle", callback_data="combo_shuffle"),  
            types.InlineKeyboardButton("▶️ START", callback_data="combo_start")  
        )  
          
        text = f"""<b>Gateway: #PayPal_Donation ($5.00)  
By: @{session['username']}  
📁 Cards: {len(session['cards'])} (shuffled)</b>"""  
          
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)  
      
    elif call.data == "combo_stop":  
        if user_id in users_checking_files:  
            stopuser[user_id] = True  
            users_checking_files[user_id]['running'] = False  
            bot.answer_callback_query(call.id, "⏹️ Stopping...")  
            
            # Restore original buttons
            session = users_checking_files[user_id]
            markup = types.InlineKeyboardMarkup(row_width=2)  
            markup.add(  
                types.InlineKeyboardButton("🧹 Clean", callback_data="combo_clean"),  
                types.InlineKeyboardButton("🔀 Shuffle", callback_data="combo_shuffle"),  
                types.InlineKeyboardButton("▶️ START", callback_data="combo_start")  
            )  
            text = f"""<b>Gateway: #PayPal_Donation ($5.00)  
By: @{session['username']}  
📁 Cards: {len(session['cards'])} / {session['original_count']}</b>"""  
            bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)
        else:  
            bot.answer_callback_query(call.id, "❌ No active session")  
              
    elif call.data == "get_charged":  
        if user_id not in users_checking_files:  
            bot.answer_callback_query(call.id, "❌ No session")  
            return  
          
        hits = users_checking_files[user_id].get('charged', [])  
        if not hits:  
            bot.answer_callback_query(call.id, "No charged cards")  
            return  
          
        bot.answer_callback_query(call.id)  
        hits_content = '\n'.join(hits)  
        filename = f"charged_{len(hits)}.txt"  
          
        with open(filename, 'w') as f:  
            f.write(hits_content)  
          
        with open(filename, 'rb') as f:  
            bot.send_document(chat_id, f, caption=f"<b>🔥 Charged: {len(hits)}</b>", parse_mode="HTML")  
          
        os.remove(filename)  
          
    elif call.data == "get_approved":  
        if user_id not in users_checking_files:  
            bot.answer_callback_query(call.id, "❌ No session")  
            return  
          
        ccn = users_checking_files[user_id].get('approved', [])  
        if not ccn:  
            bot.answer_callback_query(call.id, "No approved cards")  
            return  
          
        bot.answer_callback_query(call.id)  
        ccn_content = '\n'.join(ccn)  
        filename = f"approved_{len(ccn)}.txt"  
          
        with open(filename, 'w') as f:  
            f.write(ccn_content)  
          
        with open(filename, 'rb') as f:  
            bot.send_document(chat_id, f, caption=f"<b>✅ Approved: {len(ccn)}</b>", parse_mode="HTML")  
          
        os.remove(filename)  
          
    elif call.data == "get_declined":  
        if user_id not in users_checking_files:  
            bot.answer_callback_query(call.id, "❌ No session")  
            return  
          
        dead = users_checking_files[user_id].get('declined', [])  
        if not dead:  
            bot.answer_callback_query(call.id, "No declined cards")  
            return  
          
        bot.answer_callback_query(call.id)  
        dead_content = '\n'.join(dead)  
        filename = f"declined_{len(dead)}.txt"  
          
        with open(filename, 'w') as f:  
            f.write(dead_content)  
          
        with open(filename, 'rb') as f:  
            bot.send_document(chat_id, f, caption=f"<b>❌ Declined: {len(dead)}</b>", parse_mode="HTML")  
          
        os.remove(filename)  
    
    # ========== OTHER CALLBACKS ==========
    elif call.data == "commands":  
        text = f"""<b>  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] 📋 Commands List  
- - - - - - - - - - - - - - - - - - - - - -  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] /start - Start the bot  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] /pp - Check single card (0.5 points)  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] /bin - BIN lookup  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] /myamount - Set check amount  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] /mypoints - Check your balance  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] /subscribe - Buy subscription  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] /status - Check subscription status  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] Upload .txt - Combo check  
- - - - - - - - - - - - - - - - - - - - - -  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] Format: cc|mm|yy|cvv  
- - - - - - - - - - - - - - - - - - - - - -  
</b>"""  
        bot.answer_callback_query(call.id)  
        bot.send_message(chat_id, text, parse_mode="HTML")  
          
    elif call.data == "info":  
        sub_status = get_remaining_time(user_id)  
        text = f"""<b>  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] ℹ️ Bot Info  
- - - - - - - - - - - - - - - - - - - - - -  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] 🌐 Gateway: PayPal $5.00  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] ⏰ Balance: {sub_status}  
- - - - - - - - - - - - - - - - - - - - - -  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] 👨‍💻 Developer: {OWNER_NAME}  
[<a href="https://t.me/{OWNER_USERNAME}">ϟ</a>] 📱 Username: @{OWNER_USERNAME}  
- - - - - - - - - - - - - - - - - - - - - -  
</b>"""  
        bot.answer_callback_query(call.id)  
        bot.send_message(chat_id, text, parse_mode="HTML")  
      
    elif call.data == "subscribe":  
        bot.answer_callback_query(call.id)  
        sub_status = get_remaining_time(user_id)  
          
        markup = types.InlineKeyboardMarkup(row_width=1)  
        markup.add(  
            types.InlineKeyboardButton("⏰ 1 Hour (15⭐)", callback_data="sub_1h"),  
            types.InlineKeyboardButton("⏰ 24 Hours (70⭐)", callback_data="sub_24h"),  
            types.InlineKeyboardButton("🔙 Back", callback_data="back_main")  
        )  
          
        text = f"""<b>  
[ϟ] Buy Subscription ⏰  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] Current Balance: {sub_status}  
- - - - - - - - - - - - - - - - - - - - - -  
⏰ Hourly Subscriptions (Unlimited Checks):  
[ϟ] 1 Hour = 15⭐  
[ϟ] 24 Hours = 70⭐  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] Pay with Telegram Stars ⭐  
</b>"""  
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="HTML", reply_markup=markup)  
      
    elif call.data == "bin_lookup":  
        bot.answer_callback_query(call.id)  
        bot.send_message(chat_id, "<b>🔍 Send BIN number to look up:\nExample: /bin 414720</b>", parse_mode="HTML")  
      
    elif call.data == "my_balance":  
        bot.answer_callback_query(call.id)  
        my_points_command(call.message)  
      
    elif call.data == "owner_info":  
        bot.answer_callback_query(call.id)  
        text = f"""<b>👨‍💻 Developer Information</b>  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] <b>Name:</b> {OWNER_NAME}  
[ϟ] <b>Username:</b> @{OWNER_USERNAME}  
[ϟ] <b>ID:</b> <code>{OWNER_ID}</code>  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] <b>Support:</b> Contact @{OWNER_USERNAME} for help  
[ϟ] <b>Buy Points:</b> Use /subscribe  
- - - - - - - - - - - - - - - - - - - - - -  
[⌤] <b>Dev by: {OWNER_NAME} - @{OWNER_USERNAME} 🗣</b>"""  
        bot.send_message(chat_id, text, parse_mode="HTML")  
      
    elif call.data.startswith("sub_"):  
        handle_subscription(call)  
      
    elif call.data == "back_main":  
        bot.answer_callback_query(call.id)  
        start_handler(call.message)  
      
    elif call.data == "none":  
        bot.answer_callback_query(call.id)  

# ============================================  
# Handle Reply Keyboard Buttons  
# ============================================  

@bot.message_handler(func=lambda message: message.text == "📁 Combo Check")  
def handle_combo_button(message):  
    bot.reply_to(message, "<b>📁 Please upload a .txt file with cards\nFormat: cc|mm|yy|cvv</b>", parse_mode="HTML")  

@bot.message_handler(func=lambda message: message.text == "💳 Single Check")  
def handle_single_button(message):  
    bot.reply_to(message, "<b>💳 Send card:\n<code>/pp 1234567890123456|12|25|123</code></b>", parse_mode="HTML")  

@bot.message_handler(func=lambda message: message.text == "🔎 BIN Lookup")  
def handle_bin_lookup_button(message):  
    bot.reply_to(message, "<b>🔍 Send BIN number:\n<code>/bin 414720</code></b>", parse_mode="HTML")  

@bot.message_handler(func=lambda message: message.text == "⭐ My Balance")  
def handle_balance_button(message):  
    my_points_command(message)  

@bot.message_handler(func=lambda message: message.text == "❓ Help")  
def handle_help_button(message):  
    help_command(message)  

@bot.message_handler(func=lambda message: message.text == "👨‍💻 Owner")  
def handle_owner_button(message):  
    text = f"""<b>👨‍💻 Developer Information</b>  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] <b>Name:</b> {OWNER_NAME}  
[ϟ] <b>Username:</b> @{OWNER_USERNAME}  
[ϟ] <b>ID:</b> <code>{OWNER_ID}</code>  
- - - - - - - - - - - - - - - - - - - - - -  
[ϟ] <b>Support:</b> Contact @{OWNER_USERNAME} for help  
- - - - - - - - - - - - - - - - - - - - - -  
[⌤] <b>Dev by: {OWNER_NAME} - @{OWNER_USERNAME} 🗣</b>"""  
    bot.reply_to(message, text, parse_mode="HTML")  

# ============================================  
# Start Bot  
# ============================================  

if __name__ == "__main__":
    print("="*50)
    print("Bot Started Successfully!")
    print(f"Owner: {OWNER_NAME} (@{OWNER_USERNAME})")
    print(f"Owner ID: {OWNER_ID}")
    print(f"Gateway: PayPal Donation ($5.00)")
    print("="*50)
    bot.infinity_polling(timeout=80)
