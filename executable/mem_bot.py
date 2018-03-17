from bot_settings import *
import vk_api
import telebot
import os
import wget
import psycopg2


class MemyProKotovBot:
    def __init__(self):
        self.vk_session = vk_api.VkApi(VK_LOGIN, VK_PASSWORD)
        self.vk_session.auth()       
        self.vk = self.vk_session.get_api()

        self._db_conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        self._db_cursor = self._db_conn.cursor()
        
        self.bot = telebot.TeleBot(TOKEN)
        self._add_handlers()

    def _parse_response(self, response):
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
    
    def _get_last_post(self, api_response):
        first_post = api_response['items'][0]
        second_post = api_response['items'][1]

        if 'is_pinned' in first_post.keys():
            return second_post['id']
        return first_post['id']

    def _send_retrieved_posts(self, posts, chat):
        for r in posts:
            text = r[0]
            if len(r) > 1:
                try:
                    if len(r) == 2:
                        # self.bot.send_photo(message.chat.id, r[1], caption=text)
                        if len(text) < 200:
                            self.bot.send_photo(chat.id, r[1], caption=text)
                        else:
                            self.bot.send_photo(chat.id, r[1])
                            self.bot.send_message(chat.id, text)
                    elif len(r) > 2:
                        media = [telebot.types.InputMediaPhoto(m) for m in r[1:]]
                        self.bot.send_media_group(chat.id, media)
                        if text:
                            self.bot.send_message(chat.id, text)
            
                except Exception as exc:
                    #print("Request exception occured, but I`m still alive (" + str(exc) + ")")
                    if "group send failed" in str(exc):
                        print("Group send failed. Trying to load pictures manualy")
                        downloaded = []
                        for address in r[1:]:
                            downloaded.append(wget.download(address))
                        print("All pictures downloaded")

                        self.bot.send_media_group(chat.id, [telebot.types.InputMediaPhoto(open(d, 'rb')) for d in downloaded])
                        print("Done.")
                        for d in downloaded:
                            os.remove(d)
                        print("temporary files heve been removed")
            else:
                if text:
                    self.bot.send_message(chat.id, text)

    def send_posts(self, message, count):
        response = self.vk.wall.get(domain=PUBLIC_DOMEN, count=count)
        result = self._parse_response(response)
        self._send_retrieved_posts(result, message.chat)
        
        
    def _user_registered(self, user):
        self._db_cursor.execute("""SELECT * from users WHERE user_id = """ + str(user.id))

        rows = self._db_cursor.fetchall()
        if len(rows) == 0:
            return False
        return True
    def _register_user(self, user_id, last_post_id):
        self._db_cursor.execute("INSERT INTO users VALUES({0}, {1})".format(str(user_id), str(last_post_id)))
    def _add_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start_work(message):
            #self.send_posts(message, 5)
            if self._user_registered(message.from_user):
                #Get last post id and retrieve all post until this value
                self._db_cursor.execute("""SELECT last_post FROM users WHERE user_id = """ + str(message.from_user.id))
                res = self._db_cursor.fetchall()
                self.bot.send_message(message.chat.id, "You are registered. Your last post is " + str(res[0][0]))
            else:
                #Retrieve last 10 posts and add a user to DB with last post id
                response = self.vk.wall.get(domain=PUBLIC_DOMEN, count=10)
                last_post = self._get_last_post(response)
                result = self._parse_response(response)
                self._send_retrieved_posts(result, message.chat)

                self._register_user(message.from_user.id, last_post)

                self.bot.send_message(message.chat.id, "You are now registered with id " + str(message.from_user.id) + " and last post " + str(last_post))


        @self.bot.message_handler(commands=['shitty_update'])
        def update_work(message):
            self.send_posts(message, 5)

        @self.bot.message_handler(commands=['stop'])
        def stop_work(message):
            print(message.from_user.first_name + "stoped sending.")

        
    def updates_listener_start(self):
        self.bot.polling()
