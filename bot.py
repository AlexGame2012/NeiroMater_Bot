import os
import io
import time
import telebot
from dotenv import load_dotenv
from logic import ask_gpt, generate_image
from PIL import Image
import io
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_sessions = {}

@bot.message_handler(commands=['start'])
def start_message(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🧠 GPT-4o (текст)", callback_data="model_gpt"),
        InlineKeyboardButton("🎨 Leonardo AI (картинки)", callback_data="model_leo")
    )
    
    bot.reply_to(message, 
        "🎨 **Привет! Я бот с двумя нейросетями!**\n\n"
        "Выбери режим работы 👇\n\n"
        "🧠 **GPT-4o** - отвечаю на вопросы (помню диалог)\n"
        "🎨 **Leonardo AI** - рисую картинки", 
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['help'])
def help_message(message):
    current_model = "не выбран"
    if message.chat.id in user_sessions:
        model = user_sessions[message.chat.id].get("model")
        current_model = "🧠 GPT-4o" if model == "gpt" else "🎨 Leonardo AI"
    
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🧠 GPT-4o", callback_data="model_gpt"),
        InlineKeyboardButton("🎨 Leonardo AI", callback_data="model_leo")
    )
    keyboard.row(
        InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history")
    )
    
    bot.reply_to(message,
        f"📋 **Текущий режим:** {current_model}\n\n"
        "🔹 **GPT-4o** - просто пиши, я отвечаю и помню диалог\n"
        "🔹 **Leonardo AI** - просто пиши, я рисую картинку\n"
        "🔹 **Очистить историю** - забыть весь предыдущий диалог\n\n"
        "Примеры:\n"
        "• В режиме GPT: *Расскажи про космос*\n"
        "• В режиме Leonardo: *Кот в космосе*",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    
    if call.data == "model_gpt":
        if chat_id not in user_sessions:
            user_sessions[chat_id] = {"model": "gpt", "messages": []}
        else:
            user_sessions[chat_id]["model"] = "gpt"
        
        bot.answer_callback_query(call.id, "Режим GPT-4o активирован!")
        bot.send_chat_action(chat_id, 'typing')
        time.sleep(1)
        
        bot.edit_message_text(
            "🧠 **Режим GPT-4o активирован!**\n\n"
            "Теперь я буду отвечать на все твои вопросы.\n"
            "Я **запоминаю** весь диалог, чтобы отвечать по контексту.\n\n"
            "Просто напиши мне что-нибудь!",
            chat_id,
            message_id,
            parse_mode='Markdown'
        )
        
    elif call.data == "model_leo":
        if chat_id not in user_sessions:
            user_sessions[chat_id] = {"model": "leo", "messages": []}
        else:
            user_sessions[chat_id]["model"] = "leo"
        
        bot.answer_callback_query(call.id, "Режим Leonardo AI активирован!")
        bot.send_chat_action(chat_id, 'typing')
        time.sleep(1)
        
        bot.edit_message_text(
            "🎨 **Режим Leonardo AI активирован!**\n\n"
            "Теперь на любое твоё сообщение я буду рисовать картинку.\n"
            "Например: *красивый закат в горах*",
            chat_id,
            message_id,
            parse_mode='Markdown'
        )
        
    elif call.data == "clear_history":
        if chat_id in user_sessions:
            user_sessions[chat_id]["messages"] = []
            bot.answer_callback_query(call.id, "История очищена!")
            
            bot.send_chat_action(chat_id, 'typing')
            time.sleep(1)
            
            bot.edit_message_text(
                "🗑️ **История диалога очищена!**\n\n"
                "Теперь я ничего не помню из прошлых сообщений.",
                chat_id,
                message_id,
                parse_mode='Markdown'
            )
        else:
            bot.answer_callback_query(call.id, "История пуста")

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    user_input = message.text
    
    if chat_id not in user_sessions:
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("🧠 GPT-4o", callback_data="model_gpt"),
            InlineKeyboardButton("🎨 Leonardo AI", callback_data="model_leo")
        )
        
        bot.send_chat_action(chat_id, 'typing')
        time.sleep(1)
        
        bot.reply_to(
            message, 
            "⚠️ **Сначала выбери режим работы!**", 
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return
    
    current_model = user_sessions[chat_id].get("model")
    
    if current_model == "gpt":
        handle_gpt_mode(message, chat_id, user_input)
    elif current_model == "leo":
        handle_leo_mode(message, chat_id, user_input)

def handle_gpt_mode(message, chat_id, user_input):
    bot.send_chat_action(chat_id, 'typing')
    time.sleep(1)
    
    thinking_msg = bot.reply_to(message, "Думаю...")
    
    messages = user_sessions[chat_id].get("messages", [])
    messages.append({"role": "user", "content": user_input})
    
    answer = ask_gpt(messages)
    
    time.sleep(0.5)
    bot.delete_message(chat_id, thinking_msg.message_id)
    
    if answer:
        messages.append({"role": "assistant", "content": answer})
        
        if len(messages) > 30:
            messages = messages[-30:]
        
        user_sessions[chat_id]["messages"] = messages
        
        bot.send_chat_action(chat_id, 'typing')
        time.sleep(0.5)
        
        lines = answer.split('\n')
        formatted_lines = []
        for line in lines:
            if line.startswith('### '):
                formatted_lines.append(f"**{line[4:]}**")
            elif line.startswith('## '):
                formatted_lines.append(f"**{line[3:]}**")
            elif line.startswith('# '):
                formatted_lines.append(f"**{line[2:]}**")
            else:
                formatted_lines.append(line)
        
        formatted_answer = '\n'.join(formatted_lines)
        
        bot.send_message(chat_id, formatted_answer, parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ Не удалось получить ответ")

def handle_leo_mode(message, chat_id, user_input):
    bot.send_chat_action(chat_id, 'typing')
    time.sleep(1)
    
    generating_msg = bot.reply_to(
        message, 
        f"🎨 Рисую: {user_input}\n\n⏳ 30-40 секунд..."
    )
    
    image_bytes = generate_image(user_input)
    
    time.sleep(0.5)
    bot.delete_message(chat_id, generating_msg.message_id)
    
    if image_bytes:
        
        img = Image.open(io.BytesIO(image_bytes))
        max_size = (800, 800)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        bot.send_photo(
            chat_id,
            photo=output,
            caption=f"✨ {user_input}",
            timeout=30
        )
    else:
        bot.reply_to(message, "❌ Не удалось нарисовать картинку")

@bot.message_handler(func=lambda message: message.text.lower() in ['меню', 'menu', 'выбрать модель', 'модель', 'режим'])
def show_menu(message):
    chat_id = message.chat.id
    
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("🧠 GPT-4o", callback_data="model_gpt"),
        InlineKeyboardButton("🎨 Leonardo AI", callback_data="model_leo")
    )
    
    if chat_id in user_sessions and len(user_sessions[chat_id].get("messages", [])) > 0:
        keyboard.row(
            InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history")
        )
    
    bot.send_chat_action(chat_id, 'typing')
    time.sleep(1)
    
    bot.reply_to(
        message, 
        "📋 **Меню выбора модели:**", 
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

if __name__ == "__main__":
    bot.infinity_polling()