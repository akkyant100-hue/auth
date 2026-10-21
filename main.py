import discord
from discord.ext import commands
from flask import Flask, request, jsonify
import threading
import json
import os
import base64

# === НАСТРОЙКИ ===
ENCRYPTED_TOKEN = "TVRVMk1qTTVORFF6TWpRMU5EVXpNekU1TVEuRzFvMkJuLmFna2JQOEpwdGxhemo1ZEVJNGE1RUNYbV8zQll1Mm1PNlBrME9Z"
TOKEN = base64.b64decode(ENCRYPTED_TOKEN).decode('utf-8')

DB_FILE = 'keys.json'

# === БАЗА ДАННЫХ ===
if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f:
        json.dump({}, f)

def load_db():
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# === DISCORD БОТ ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен и готов к работе!')

@bot.command()
async def addkey(ctx, key: str, hwid: str):
    db = load_db()
    db[key] = hwid
    save_db(db)
    await ctx.send(f"✅ Ключ `{key}` успешно привязан к HWID `{hwid}`")

@bot.command()
async def delkey(ctx, key: str):
    db = load_db()
    if key in db:
        del db[key]
        save_db(db)
        await ctx.send(f"🗑️ Ключ `{key}` удален.")
    else:
        await ctx.send(f"❌ Ключ `{key}` не найден.")

@bot.command()
async def keys(ctx):
    db = load_db()
    if not db:
        await ctx.send("База ключей пуста.")
    else:
        msg = "**Активные ключи:**\n"
        for k, v in db.items():
            msg += f"`{k}` -> `{v}`\n"
        await ctx.send(msg)

# === FLASK СЕРВЕР (Для Xeno) ===
app = Flask(__name__)

@app.route('/api/check', methods=['GET'])
def check():
    key = request.args.get('key')
    hwid = request.args.get('hwid')
    
    if not key or not hwid:
        return jsonify({"valid": False, "message": "Missing params"}), 400
    
    db = load_db()
    
    if key in db:
        if db[key] == hwid:
            return jsonify({"valid": True})
        else:
            return jsonify({"valid": False, "message": "HWID mismatch (Key used on another PC)"}), 403
    else:
        return jsonify({"valid": False, "message": "Invalid Key"}), 403

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# === ЗАПУСК ===
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
