import discord
from discord.ext import commands
from flask import Flask, request, jsonify
import threading
import os
import base64
import sqlite3

# === НАСТРОЙКИ ===
ENCRYPTED_TOKEN = "TVRVMk1qTTVORFF6TWpRMU5EVXpNekU1TVEuRzFvMkJuLmFna2JQOEpwdGxhemo1ZEVJNGE1RUNYbV8zQll1Mm1PNlBrME9Z"
TOKEN = base64.b64decode(ENCRYPTED_TOKEN).decode('utf-8')
DB_FILE = 'database.db'

# === ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ===
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Таблица хранит ключ и привязанный к нему HWID
    c.execute('''CREATE TABLE IF NOT EXISTS keys (key TEXT PRIMARY KEY, hwid TEXT)''')
    conn.commit()
    conn.close()

init_db()

def add_key_db(key, hwid="None"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO keys (key, hwid) VALUES (?, ?)", (key, hwid))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def del_key_db(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM keys WHERE key = ?", (key,))
    conn.commit()
    conn.close()

def check_and_bind_key(key, hwid):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT hwid FROM keys WHERE key = ?", (key,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return False, "Invalid Key"
        
    saved_hwid = result[0]
    
    # Если ключ еще не привязан (или был создан без HWID), привязываем его
    if saved_hwid == "None" or saved_hwid == "":
        c.execute("UPDATE keys SET hwid = ? WHERE key = ?", (hwid, key))
        conn.commit()
        conn.close()
        return True, "Key bound to HWID successfully"
        
    # Если HWID совпадает — пускаем
    if saved_hwid == hwid:
        conn.close()
        return True, "Valid"
    else:
        conn.close()
        return False, "HWID Mismatch (Key used on another PC)"

def get_all_keys():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, hwid FROM keys")
    result = c.fetchall()
    conn.close()
    return result

# === DISCORD БОТ ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен и готов к работе!')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Ошибка:** Не хватает аргументов!\nПравильный формат: `!addkey КЛЮЧ`")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"⚠️ **Ошибка в боте:** `{str(error)}`")

@bot.command()
async def addkey(ctx, key: str):
    if add_key_db(key):
        print(f"[БАЗА] Добавлен ключ: {key}")
        await ctx.send(f"✅ Ключ `{key}` успешно добавлен в базу! (HWID привяжется при первом входе)")
    else:
        await ctx.send(f"⚠️ Ключ `{key}` уже существует.")

@bot.command()
async def delkey(ctx, key: str):
    del_key_db(key)
    print(f"[БАЗА] Удален ключ: {key}")
    await ctx.send(f"🗑️ Ключ `{key}` удален.")

@bot.command()
async def keys(ctx):
    db_keys = get_all_keys()
    if not db_keys:
        await ctx.send("База ключей пуста.")
    else:
        msg = "**Активные ключи (Ключ -> HWID):**\n"
        for k, hwid in db_keys:
            msg += f"`{k}` -> `{hwid}`\n"
        await ctx.send(msg)

# === FLASK СЕРВЕР ===
app = Flask(__name__)

@app.route('/api/check', methods=['GET'])
def check():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    
    if not key or not hwid:
        return jsonify({"valid": False, "message": "Missing key or HWID"}), 400
    
    success, message = check_and_bind_key(key, hwid)
    
    if success:
        print(f"[ПРОВЕРКА] Успешный вход: {key} | HWID: {hwid}")
        return jsonify({"valid": True, "message": message})
    else:
        print(f"[ПРОВЕРКА] Отказ: {message} | Key: {key} | HWID: {hwid}")
        return jsonify({"valid": False, "message": message}), 403

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
