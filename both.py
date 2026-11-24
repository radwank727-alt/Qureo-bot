import sqlite3
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = "9268591039:AAEXLdWufRH8VpZ7pClk24y5Knwbc_lQ5JA"
bot = telebot.TeleBot(TOKEN)

conn = sqlite3.connect("bot_data.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users
(user_id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, invited_by INTEGER)""")
cursor.execute("""CREATE TABLE IF NOT EXISTS settings
(key TEXT PRIMARY KEY, value TEXT)""")
conn.commit()

def get_admin_id():
cursor.execute("SELECT value FROM settings WHERE key = 'admin_id'")
row = cursor.fetchone()
return int(row[0]) if row else None

@bot.message_handler(commands=["admin_me"])
def claim_admin(message):
current_admin = get_admin_id()
if current_admin is None:
cursor.execute(
"INSERT INTO settings (key, value) VALUES ('admin_id', ?)",
(str(message.from_user.id),),
)
conn.commit()
bot.reply_to(
message,
"✅ تم تسجيلك كأدمن رسمي للبوت بنجاح! اضغط /start لعرض لوحة التحكم.",
)
elif current_admin == message.from_user.id:
bot.reply_to(message, "أنت بالفعل الأدمن المسجل للبوت.")
else:
bot.reply_to(message, "❌ يوجد أدمن مسجل بالفعل لهذا البوت.")

@bot.message_handler(commands=["start"])
def send_welcome(message):
user_id = message.from_user.id
args = message.text.split()

cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
user = cursor.fetchone()

if not user:
invited_by = None
if len(args) > 1 and args[1].startswith("r"):
try:
invited_by = int(args[1][1:])
if invited_by != user_id:
cursor.execute(
"UPDATE users SET points = points + 1 WHERE user_id = ?",
(invited_by,),
)
try:
bot.send_message(
invited_by,
"🎉 مبروك! شخص جديد دخل من رابطك وحصلت على +1 نقطة.",
)
except Exception:
pass
except ValueError:
pass

cursor.execute(  
    "INSERT INTO users (user_id, points, invited_by) VALUES (?, ?, ?)",  
    (user_id, 0, invited_by),  
)  
conn.commit()

markup = InlineKeyboardMarkup(row_width=2)
btn1 = InlineKeyboardButton("📚 الصف الأول الثانوي", callback_data="grade_1")
btn2 = InlineKeyboardButton("📖 الصف الثاني الثانوي", callback_data="grade_2")
btn3 = InlineKeyboardButton("💰 رصيدي ونقاطي", callback_data="my_points")
btn4 = InlineKeyboardButton("🔗 رابط الإحالة", callback_data="ref_link")
markup.add(btn1, btn2, btn3, btn4)

if user_id == get_admin_id():
btn_admin = InlineKeyboardButton(
"⚙️ لوحة تحكم الأدمن", callback_data="admin_panel"
)
markup.add(btn_admin)

bot.send_message(
message.chat.id,
"👋 أهلاً بك في البوت التعليمي!\nاختر القسم المناسب من القائمة:",
reply_markup=markup,
)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
user_id = call.from_user.id
admin_id = get_admin_id()

if call.data == "my_points":
cursor.execute("SELECT points FROM users WHERE user_id = ?", (user_id,))
res = cursor.fetchone()
pts = res[0] if res else 0
bot.answer_callback_query(
call.id, f"رصيدك الحالي هو: {pts} نقطة", show_alert=True
)

elif call.data == "ref_link":
bot_username = bot.get_me().username
link = f"https://t.me/{bot_username}?start=r{user_id}"
bot.send_message(
call.message.chat.id,
f"🔗 شارك رابطك الخاص واكسب نقاط مجانية على كل دعوة:\n\n{link}",
parse_mode="Markdown",
)

elif call.data in ["grade_1", "grade_2"]:
bot.send_message(
call.message.chat.id,
"📂 هذا القسم جاهز لإضافة الشروحات والملفات التعليمية.",
)

elif call.data == "admin_panel" and user_id == admin_id:
cursor.execute("SELECT COUNT(*) FROM users")
total_users = cursor.fetchone()[0]
admin_markup = InlineKeyboardMarkup()
admin_markup.add(
InlineKeyboardButton("📢 إذاعة رسالة للكل", callback_data="broadcast")
)
bot.send_message(
call.message.chat.id,
f"📊 إحصائيات البوت:\n👥 عدد المشتركين: {total_users} عضو",
parse_mode="Markdown",
reply_markup=admin_markup,
)

elif call.data == "broadcast" and user_id == admin_id:
msg = bot.send_message(
call.message.chat.id,
"✍️ ابعت الرسالة اللي عاوز تبعتها لكل مستخدمين البوت دلوقتي:",
)
bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
cursor.execute("SELECT user_id FROM users")
users = cursor.fetchall()
count = 0
for u in users:
try:
bot.send_message(u[0], message.text)
count += 1
except Exception:
pass
bot.send_message(message.chat.id, f"✅ تم إرسال رسالتك بنجاح إلى {count} عضو.")

print("Bot is running...")
bot.infinity_polling()
