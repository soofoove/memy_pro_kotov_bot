import telebot

TOKEN = "574980005:AAEpFevnWRl6m3GYzFYFMhULbX2FCp8xmZg"

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def proc_simple_message(message):
    bot.reply_to(message, 'bot testing message')

bot.polling()