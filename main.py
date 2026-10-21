import discord
from discord.ext import commands
from flask import Flask, request, jsonify
import threading
import json
import os
import base64

# === НАСТРОЙКИ ===
# Твой токен, зашифрованный в Base64
ENCRYPTED_TOKEN = "TVRVMk1qTTVORFF6TWpRMU5EVXpNekU1TVEuRzFvMkJuLmFna2JQOEpwdGxhemo1ZEVJNGE1RUNYbV8zQll1Mm1PNlBrME9Z"
TOKEN = base64.b64decode(ENCRYPTED_TOKEN).decode('utf-8')
DB_FILE = 'keys.json'

# === БАЗА ДАННЫХ ===
if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w') as f:
        json.dump([], f) # Теперь это список, а не словарь

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

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ **Ошибка:** Не хватает аргументов!\nПравильный формат: `!addkey КЛЮЧ`")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"Ошибка: {error}")

@bot.command()
async def addkey(ctx, key: str):
    db = load_db()
    if key in db:
        await ctx.send(f"⚠️ Ключ `{key}` уже существует.")
        return
    
    db.append(key)
    save_db(db)
    await ctx.send(f"✅ Ключ `{key}` успешно добавлен в базу!")

@bot.command()
async def delkey(ctx, key: str):
    db = load_db()
    if key in db:
        db.remove(key)
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
        for k in db:
            msg += f"`{k}`\n"
        await ctx.send(msg)

# === FLASK СЕРВЕР (Для Xeno) ===
app = Flask(__name__)

@app.route('/api/check', methods=['GET'])
def check():
    key = request.args.get('key')
    
    if not key:
        return jsonify({"valid": False, "message": "Missing key"}), 400
    
    db = load_db()
    
    if key in db:
        return jsonify({"valid": True})
    else:
        return jsonify({"valid": False, "message": "Invalid Key"}), 403

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# === ЗАПУСК ===
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    bot.run(TOKEN)
