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

# === БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS keys (key TEXT PRIMARY KEY, hwid TEXT)''')
    conn.commit()
    conn.close()

init_db()

def add_key_db(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO keys (key, hwid) VALUES (?, ?)", (key, "None"))
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
    
    if saved_hwid == "None" or saved_hwid == "" or saved_hwid is None:
        c.execute("UPDATE keys SET hwid = ? WHERE key = ?", (hwid, key))
        conn.commit()
        conn.close()
        return True, "Bound to HWID"
        
    if saved_hwid == hwid:
        conn.close()
        return True, "Valid"
    else:
        conn.close()
        return False, "HWID Mismatch (Key used on another PC)"

# === БОТ ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')

@bot.command()
async def addkey(ctx, key: str):
    if add_key_db(key):
        await ctx.send(f"✅ Ключ `{key}` добавлен! (HWID привяжется при входе)")
    else:
        await ctx.send(f"⚠️ Ключ `{key}` уже существует.")

@bot.command()
async def delkey(ctx, key: str):
    del_key_db(key)
    await ctx.send(f"🗑️ Ключ `{key}` удален.")

@bot.command()
async def keys(ctx):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT key, hwid FROM keys")
    result = c.fetchall()
    conn.close()
    if not result:
        await ctx.send("База пуста.")
    else:
        msg = "**Ключи:**\n"
        for k, hwid in result:
            msg += f"`{k}` -> `{hwid}`\n"
        await ctx.send(msg)

# === СЕРВЕР ===
app = Flask(__name__)

@app.route('/api/check', methods=['GET'])
def check():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    
    if not key or not hwid:
        # Вместо 400 возвращаем 200, чтобы скрипт прочитал JSON
        return jsonify({"valid": False, "message": "Missing key or HWID"})
    
    success, message = check_and_bind_key(key, hwid)
    
    if success:
        print(f"[УСПЕХ] {key} | {hwid}")
        return jsonify({"valid": True, "message": message})
    else:
        print(f"[ОТКАЗ] {message} | Key: {key}")
        # ВАЖНО: Мы убрали код 403. Теперь всегда отдаем 200 OK.
        return jsonify({"valid": False, "message": message})

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
