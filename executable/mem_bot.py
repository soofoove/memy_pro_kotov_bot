from bot_settings import *
import BD_Accessor
import VK_Group
import vk_api
import telebot
import os
import wget
import psycopg2
import threading
import time


class MemyProKotovBot:
    def __init__(self):
        self.users = []
        self.last_post = 0

        self.waiting_for_users = True

        self.vk_session = vk_api.VkApi(VK_LOGIN, VK_PASSWORD)
        self.vk_session.auth()       
        # self.vk = self.vk_session.get_api()

        self.__group = VK_Group.VkGroup(self.vk_session.get_api())
        self.__ac = BD_Accessor.Accessor()

        self._start_first_init()
        
        self.bot = telebot.TeleBot(TOKEN)
        self._add_handlers()

    def _start_first_init(self):
        self.users = self.__ac.get_all_users()
        self.last_post = self.__ac.get_last_post()

        print("Data loaded from DB")

    def _send_retrieved_posts(self, posts, chat_id):
        for r in posts:
            text = r[0]
            if len(r) > 1:
                try:
                    if len(r) == 2:
                        # self.bot.send_photo(message.chat.id, r[1], caption=text)
                        if len(text) < 200:
                            self.bot.send_photo(chat_id, r[1], caption=text)
                        else:
                            self.bot.send_photo(chat_id, r[1])
                            self.bot.send_message(chat_id, text)
                    elif len(r) > 2:
                        media = [telebot.types.InputMediaPhoto(m) for m in r[1:]]
                        self.bot.send_media_group(chat_id, media)
                        if text:
                            self.bot.send_message(chat_id, text)
            
                except Exception as exc:
                    #print("Request exception occured, but I`m still alive (" + str(exc) + ")")
                    if "group send failed" in str(exc):
                        print("Group send failed. Trying to load pictures manualy")
                        downloaded = []
                        for address in r[1:]:
                            downloaded.append(wget.download(address))
                        print("All pictures downloaded")

                        self.bot.send_media_group(chat_id, [telebot.types.InputMediaPhoto(open(d, 'rb')) for d in downloaded])
                        print("Done.")
                        for d in downloaded:
                            os.remove(d)
                        print("temporary files heve been removed")
            else:
                if text:
                    self.bot.send_message(chat_id, text)

    def send_posts(self, message, count):
        result = self.__group.get_posts(count)
        self._send_retrieved_posts(result, message.chat)
    
    # def _is_new_post(self, chat):
    #     last_post = self.__ac.get_last_post(chat)
    #     response = self.vk.wall.get(domain=PUBLIC_DOMEN, count=2)

    #     first = response['items'][0]
    #     second = response['items'][1]

    #     if 'is_pinned' in first.keys():
    #         return second['id'] != last_post
    #     else:
    #         return first['id'] != last_post

    def _perform_vk_update_loop(self):
        print("Update loop started")
        while True:
            
            if self.__group.is_new_post(self.last_post):
                result, last_post = self.__group.retrieve_posts(self.last_post)

                for chat in self.users:
                    print(chat)
                    self._send_retrieved_posts(result, chat)

                self.__ac.set_last_post(last_post)
                self.last_post = last_post

                print("New posts were send. Last post: " + str(self.last_post))
            else:
                pass
                #self.bot.send_message(chat.id, "Новых мемесов нет")
            time.sleep(5)

    def _add_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start_work(message):
            #self.send_posts(message, 5)
            if self.__ac.user_registered(message.chat.id):
                #Get last post id and retrieve all post until this value
                # last_post = self.__ac.get_last_post(message.chat)
                self.bot.send_message(message.chat.id, "You have been already registered. Your last post is " + str(self.last_post))
            else:
                #Retrieve last 10 posts and add a user to DB with last post id
                result = self.__group.get_posts(10)
                self._send_retrieved_posts(result, message.chat.id)
                last_post = self.__group.get_last_post_id()

                self.__ac.register_user(message.chat.id)
                self.users.append(message.chat.id)

                self.bot.send_message(message.chat.id, "You are now registered with id " + str(message.chat.id) + " and last post " + str(self.last_post))
                # t = threading.Thread(target=self._perform_vk_update_loop, args=(message.chat.id, ))
                # t.start()
                if self.waiting_for_users:
                    self.__ac.set_last_post(last_post)
                    self.last_post = last_post
                    t = threading.Thread(target=self._perform_vk_update_loop)
                    t.start()
                    self.waiting_for_users = False
                self.bot.send_message(message.chat.id, "You have been subscripted for updates")

                print("User with chat_id " + str(message.chat.id) + " was registered")


        @self.bot.message_handler(commands=['update'])
        def update_work(message):
            if not self.__ac.user_registered(message.chat.id):
                self.bot.send_message(message.chat.id, "Please, do /start before")
                return
            else:
                self.bot.send_message(message.chat.id, "Команда отныне не работает")
    
    # def polling_worker(self):
    #     while True:
    #         try:
    #             self.bot.polling()
    #             print("Polling started")
    #         except requests.exceptions.Timeout as e:
    #             print("Exception occured when polling: " + str(e))
    #             print("Restarting polling.....")
    
    def updates_listener_start(self):
        poll = threading.Thread(target=self.bot.polling, kwargs=dict(none_stop=True, timeout=30))
        poll.start()
        print("Polling started")

        if len(self.users) > 0:
            t = threading.Thread(target=self._perform_vk_update_loop)
            t.start()
        else:
            print("There are no users yet. Update loop waiting for users")

        poll.join()
