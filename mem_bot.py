import vk_api
import telebot
import os
import wget

class MemyProKotovBot:
    def __init__(self):
        self.TOKEN = os.environ["BOT_TOKEN"]
        self.PUBLIC_DOMEN = "memy_pro_kotow"
        self.VK_LOGIN = os.environ["VK_LOGIN"]
        self.VK_PASSWORD = os.environ["VK_PASSWORD"]

        self.vk_session = vk_api.VkApi(self.VK_LOGIN, self.VK_PASSWORD)
        
        self.vk_session.auth()
        
            
        self.vk = self.vk_session.get_api()
        
        self.bot = telebot.TeleBot(self.TOKEN)
        self._add_handlers()

    def parse_response(self, response):
        """
        Return result in the format [text_msg, attachment1, attachment2, ...]
        """
        result = []
        
        for item in response['items']:
            if "is_pinned" in item.keys():
                continue
            temp = []
            if not item['text']:
                temp.append("")
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
    
    def send_posts(self, message, count):
        response = self.vk.wall.get(domain=self.PUBLIC_DOMEN, count=count)
        last_post = response['items'][0]['id']
        result = self.parse_response(response)
        print("Result parsed. Last post: " + str(last_post))
        for r in result:
            text = r[0]
            if len(r) > 1:
                try:
                    if len(r) == 2:
                        # self.bot.send_photo(message.chat.id, r[1], caption=text)
                        if len(text) < 200:
                            self.bot.send_photo(message.chat.id, r[1], caption=text)
                        else:
                            self.bot.send_photo(message.chat.id, r[1])
                            self.bot.send_message(message.chat.id, text)
                    elif len(r) > 2:
                        media = [telebot.types.InputMediaPhoto(m) for m in r[1:]]
                        self.bot.send_media_group(message.chat.id, media)
                        if text:
                            self.bot.send_message(message.chat.id, text)
            
                except Exception as exc:
                    #print("Request exception occured, but I`m still alive (" + str(exc) + ")")
                    if "group send failed" in str(exc):
                        print("Group send failed. Trying to load pictures manualy")
                        downloaded = []
                        for address in r[1:]:
                            downloaded.append(wget.download(address))
                        print("All pictures downloaded")

                        self.bot.send_media_group(message.chat.id, [telebot.types.InputMediaPhoto(open(d, 'rb')) for d in downloaded])
                        print("Done.")
                        for d in downloaded:
                            os.remove(d)
                        print("temporary files heve been removed")
            else:
                if text:
                    self.bot.send_message(message.chat.id, text)

        self.bot.send_message(message.chat.id, "Type /shitty_update to manual update")
        
    def _add_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start_work(message):
            self.send_posts(message, 100)

        

        @self.bot.message_handler(commands=['shitty_update'])
        def update_work(message):
            self.send_posts(message, 5)
        
    def updates_listener_start(self):
        self.bot.polling()
