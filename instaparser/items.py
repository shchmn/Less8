# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class InstaparserItem(scrapy.Item):
    _id = scrapy.Field()
    url = scrapy.Field()
    info = scrapy.Field()
    username = scrapy.Field()
    user_id = scrapy.Field()
    f_user_id = scrapy.Field()
    f_username = scrapy.Field()
    photos = scrapy.Field()
    post_photo_id = scrapy.Field()
    profile_photo = scrapy.Field()
    profile_pic_id = scrapy.Field()
    post_photo = scrapy.Field()
    post_likes = scrapy.Field()
    post_data = scrapy.Field()