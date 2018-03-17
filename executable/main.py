from mem_bot import *
import psycopg2

if __name__ == '__main__':
    try:

        MemBot = MemyProKotovBot()
        MemBot.updates_listener_start()
    except vk_api.AuthError as error_msg:
        print(error_msg) 
        