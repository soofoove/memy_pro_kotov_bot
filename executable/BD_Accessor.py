import psycopg2
import bot_settings

class _singleton:
    def __init__(self, cls):
        self.__wrapped__ = cls
        self.__instance__ = None

    def __call__(self, *args, **kwargs):
        if self.__instance__ is None:
            self.__instance__ = self.__wrapped__(*args, **kwargs)
        return self.__instance__
def singleton(cls):
    return _singleton(cls)

@singleton
class Accessor:
    def __init__(self):
        self.__conn = psycopg2.connect(bot_settings.DATABASE_URL, sslmode='require')
        self.__cursor = self.__conn.cursor()
    
    def get_last_post(self):
        self.__cursor.execute("""SELECT id FROM last_post""")
        res = self.__cursor.fetchall()

        return res[0][0]

    def set_last_post(self, last_post):
        self.__cursor.execute("""UPDATE last_post SET id = {0}""".format(last_post))

        self.__conn.commit()

    def user_registered(self, chat_id):
        self.__cursor.execute("""SELECT * from users WHERE chat_id = """ + str(chat_id))

        rows = self.__cursor.fetchall()
        if len(rows) == 0:
            return False
        return True

    def register_user(self, chat_id):
        self.__cursor.execute("INSERT INTO users VALUES({0})".format(str(chat_id)))
        self.__conn.commit()

    def get_all_users(self):
        self.__cursor.execute("""SELECT chat_id FROM users""")
        rows = self.__cursor.fetchall()
        result = [r[0] for r in rows]
        return result