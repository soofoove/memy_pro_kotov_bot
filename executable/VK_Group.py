import vk_api
from bot_settings import *


class VkGroup:
    def __init__(self, vk_API):
        self.__vk = vk_API
        self.__domen = PUBLIC_DOMEN


    def get_last_post_id(self):
        '''Returns last post id in VK public, but not considers pinned post'''
        # if len(api_response['items']) == 1:
        #     if 'is_pinned' in api_response['items'][0].keys():
        #         api_response = self.__vk.wall.get(domain=self.__domen, count=2)
        api_response = self.__vk.wall.get(domain=self.__domen, count=2)
        first_post = api_response['items'][0]
        second_post = api_response['items'][1]

        if 'is_pinned' in first_post.keys():
            return second_post['id']
        return first_post['id']

    def __parse_response(self, response):
        """
        Return result in the format: [text_msg, attachment1, attachment2, ...]
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

    def get_posts(self, count):
        '''Returns a list of parsed posts [text, photo, photo, ...]'''
        response = self.__vk.wall.get(domain=self.__domen, count=count)
        result = self.__parse_response(response)

        return result

    def retrieve_posts(self, last_post):
        new_last_post = 0
        offset = 0
        result = []
        while True:
            response = self.__vk.wall.get(domain=self.__domen, count=1, offset = offset)
            if 'is_pinned' in response['items'][0].keys():
                offset += 1
                continue
            if response['items'][0]['id'] == last_post:
                break
            offset += 1

        if offset == 0:
            return result

        response = self.__vk.wall.get(domain=self.__domen, count=offset)
        new_last_post = self.get_last_post_id()
        result = self.__parse_response(response)

        return result, new_last_post

    def is_new_post(self, last_post):
        response = self.__vk.wall.get(domain=self.__domen, count=2)

        first = response['items'][0]
        second = response['items'][1]

        if 'is_pinned' in first.keys():
            return second['id'] != last_post
        else:
            return first['id'] != last_post