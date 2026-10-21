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
        json.dump([], f)

def load_db():
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка чтения базы: {e}")
        return []

def save_db(data):
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Ошибка записи базы: {e}")

# === DISCORD БОТ ===
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен и готов к работе!')

# Ловим ВСЕ ошибки и выводим их в Discord
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Ошибка:** Не хватает аргументов!\nПравильный формат: `!addkey КЛЮЧ`")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"⚠️ **Ошибка в боте:** `{str(error)}`")
        print(f"ERROR: {error}")

@bot.command()
async def addkey(ctx, key: str):
    try:
        db = load_db()
        if key in db:
            await ctx.send(f"⚠️ Ключ `{key}` уже существует.")
            return
        
        db.append(key)
        save_db(db)
        print(f"[БАЗА] Добавлен ключ: {key}")
        await ctx.send(f"✅ Ключ `{key}` успешно добавлен в базу!")
    except Exception as e:
        await ctx.send(f"⚠️ **Ошибка при добавлении:** `{str(e)}`")
        print(f"ERROR ADDKEY: {e}")

@bot.command()
async def delkey(ctx, key: str):
    db = load_db()
    if key in db:
        db.remove(key)
        save_db(db)
        print(f"[БАЗА] Удален ключ: {key}")
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
        for k in db:
            msg += f"`{k}`\n"
        await ctx.send(msg)

# === FLASK СЕРВЕР ===
app = Flask(__name__)

@app.route('/api/check', methods=['GET'])
def check():
    key = request.args.get('key')
    if not key:
        return jsonify({"valid": False, "message": "Missing key"}), 400
    
    db = load_db()
    if key in db:
        print(f"[ПРОВЕРКА] Успешный вход: {key}")
        return jsonify({"valid": True})
    else:
        print(f"[ПРОВЕРКА] Отказ. Неверный ключ: {key}")
        return jsonify({"valid": False, "message": "Invalid Key"}), 403

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
