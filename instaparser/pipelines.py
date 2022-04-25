# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


import hashlib
import scrapy
from itemadapter import ItemAdapter
from scrapy.pipelines.images import ImagesPipeline
from pymongo import MongoClient
from scrapy.utils.python import to_bytes

class InstaparserPipeline:
    def __init__(self):
        client = MongoClient('127.0.0.1', 27017)
        self.mongobase = client.instagram

    def process_item(self, item, spider):
        if item['info'] == 'followers' or item['info'] == 'following':
            item['_id'] = hashlib.sha1(to_bytes(item['username']+item['info']+item['f_username'])).hexdigest()
        elif item['info'] == 'post':
            item['_id'] = hashlib.sha1(to_bytes(item['post_photo'])).hexdigest()
        collection = self.mongobase[item['username']][item['info']]
        if collection.find_one({'_id': item['_id']}):
            print(f'Duplicated item {item["_id"]}')
        else:
            collection.insert_one(item)
        return item


class InstaUserPhotosPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        if item['info'] == 'followers' or item['info'] == 'following':
            try:
                yield scrapy.Request(item['profile_photo'])
            except Exception as e:
                print(e)
        else:
            try:
                yield scrapy.Request(item['post_photo'])
            except Exception as e:
                print(f"Ошибка\n{e}")

    def item_completed(self, results, item, info):
        if item['info'] == 'followers' or item['info'] == 'following':
            item['profile_photo'] = [itm[1] for itm in results if itm[0]]
        return item

    def file_path(self, request, item, response=None, info=None):
        if item['info'] == 'followers' or item['info'] == 'following':
            name = item['username'].replace('/', '-')
            return f'{name}/{item["info"]}/{item["f_username"]}.jpg'
        else:
            name = item['username'].replace('/', '-')
            return f'{name}/post_photo/{item["post_photo_id"]}.jpg'
