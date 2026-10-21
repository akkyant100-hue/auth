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
    c.execute('''CREATE TABLE IF NOT EXISTS keys (key TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

init_db()

def add_key_db(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO keys (key) VALUES (?)", (key,))
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

def check_key_db(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key FROM keys WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result is not None

def get_all_keys():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key FROM keys")
    result = [row[0] for row in c.fetchall()]
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
        await ctx.send(f"✅ Ключ `{key}` успешно добавлен в базу!")
    else:
        await ctx.send(f"⚠️ Ключ `{key}` уже существует.")

@bot.command()
async def delkey(ctx, key: str):
    if check_key_db(key):
        del_key_db(key)
        print(f"[БАЗА] Удален ключ: {key}")
        await ctx.send(f"🗑️ Ключ `{key}` удален.")
    else:
        await ctx.send(f"❌ Ключ `{key}` не найден.")

@bot.command()
async def keys(ctx):
    db_keys = get_all_keys()
    if not db_keys:
        await ctx.send("База ключей пуста.")
    else:
        msg = "**Активные ключи:**\n"
        for k in db_keys:
            msg += f"`{k}`\n"
        await ctx.send(msg)

# === FLASK СЕРВЕР ===
app = Flask(__name__)

@app.route('/api/check', methods=['GET'])
def check():
    key = request.args.get('key')
    if not key:
        return jsonify({"valid": False, "message": "Missing key"}), 400
    
    if check_key_db(key):
        print(f"[ПРОВЕРКА] Успешный вход: {key}")
        return jsonify({"valid": True})
    else:
        print(f"[ПРОВЕРКА] Отказ. Неверный ключ: {key}")
        return jsonify({"valid": False, "message": "Invalid Key"}), 403

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
