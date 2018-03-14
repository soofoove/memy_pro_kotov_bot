import telebot
import vk_api
import threading
import os

TOKEN = os.environ["BOT_TOKEN"]
PUBLIC_DOMEN = "memy_pro_kotow"
VK_LOGIN = os.environ["VK_LOGIN"]
VK_PASSWORD = os.environ["VK_PASSWORD"]

def parse_response(response):
    """
    Return result in the format [text_msg, attachment1, attachment2, ...]
    """
    result = []
    
    for item in response['items']:
        temp = []
        if not item['text']:
            temp.append(None)
        else:
            temp.append(item['text'])
        
        #if item['attachments']:
        if 'attachments' in item.keys():
            for attachment in item['attachments']:
                if attachment['type'] == 'photo':
                    temp.append(attachment['photo']['photo_604'])
        result.append(temp)
    result.reverse()
    return result

def load_last_hundred(vk):
    count = 90
    result = []
    while count != 0:
        response = vk.wall.get(domain=PUBLIC_DOMEN, count=10, offset=count)
        result += parse_response(response)
        count -= 10

    return result

def main():
    vk_session = vk_api.VkApi(VK_LOGIN, VK_PASSWORD)
    try:
        vk_session.auth()
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return
    vk = vk_session.get_api()
    
    bot = telebot.TeleBot(TOKEN)

    last_post = 0

    @bot.message_handler(commands=['start'])
    def start_work(message):
        response = vk.wall.get(domain=PUBLIC_DOMEN, count=100)
        last_post = response['items'][0]['id']
        result = parse_response(response)
        print("Result parsed. Last post: " + str(last_post))
        for r in result:
            text = r[0]
            if len(r) > 1:
                try:
                    bot.send_photo(message.chat.id, r[1], caption=text) 
                except:
                    print("Request exception occured, but I`m still alive")
        
        bot.send_message(message.chat.id, "Type /shitty_update to manual update")

    

    @bot.message_handler(commands=['shitty_update'])
    def update_work(message):
        response = vk.wall.get(domain=PUBLIC_DOMEN, count=5)
        last_post = response['items'][0]['id']
        result = parse_response(response)
        print("Result parsed. Last post: " + str(last_post))
        for r in result:
            text = r[0]
            if len(r) > 1:
                try:
                    bot.send_photo(message.chat.id, r[1], caption=text) 
                except:
                    print("Request exception occured, but I`m still alive")
        
        bot.send_message(message.chat.id, "Type /shitty_update to manual update")

    bot.polling()


if __name__ == '__main__':
    main()