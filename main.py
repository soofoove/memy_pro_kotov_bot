import telebot
import vk_api
import threading
import os

TOKEN = os.getenv("BOT_TOKEN")
PUBLIC_DOMEN = "memy_pro_kotow"
VK_LOGIN = os.getenv("VK_LOGIN")
VK_PASSWORD = os.getenv("VK_PASSWORD")

def parse_response(response):
    """
    Return result in the format [text_msg, attachment1, attachment2, ...]
    """
    result = []
    if not response['items']:
        return result
    
    for item in response['items']:
        temp = []
        if not item['text']:
            temp.append(None)
        else:
            temp.append(item['text'])
        
        if item['attachments']:
            for attachment in item['attachments']:
                if attachment['type'] == 'photo':
                    temp.append(attachment['photo']['photo_604'])
        result.append(temp)

    return result


def main():
    vk_session = vk_api.VkApi(VK_LOGIN, VK_PASSWORD)
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return
    vk = vk_session.get_api()
    response = vk.wall.get(domain=PUBLIC_DOMEN, count=10)
    bot = telebot.TeleBot(TOKEN)

    @bot.message_handler(commands=['start'])
    def proc_simple_message(message):
        if response['items']:
            result = parse_response(response)
            for r in result:
                text = r[0]
                if len(r) > 1:
                    bot.send_photo(message.chat.id, r[1], caption=text) 
        
        

    bot.polling()


if __name__ == '__main__':
    main()