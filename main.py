import telebot

bot = telebot.TeleBot("TOKEN", parse_mode=None)


@bot.message_handler(content_types=['text'])
def start(message):
    if message.text == '/hello_world':
        bot.send_message(message.from_user.id, "Привет мир")
    else:
        bot.send_message(message.from_user.id, 'Напиши /hello_world')


bot.polling(none_stop=True, interval=0)
