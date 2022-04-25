import scrapy
import json
import re
from copy import deepcopy
from urllib.parse import urlencode
from scrapy.http import HtmlResponse
from instaparser.items import InstaparserItem


class IgcomSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['http://instagram.com/']
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    user_agent = 'Instagram 155.0.0.37.107'
    inst_login = 'Onliskill_udm'
    inst_pwd = 'Qw123456!!'
    ins_follow_link = 'https://i.instagram.com/api/v1/friendships/'
    follower_hash = '396983faee97f4b49ccbe105b4daf7a0'
    inst_graphql_link = 'https://www.instagram.com/graphql/query/?'
    posts_hash = '396983faee97f4b49ccbe105b4daf7a0'


    def __init__(self, name=None, **kwargs):
        super().__init__(name, **kwargs)
        self.parse_users = kwargs.get('query')


    def parse(self, response: HtmlResponse):
        csrf = self.get_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_link,
            method='POST',
            callback=self.login,
            formdata={'username': self.inst_login, 'enc_password': self.inst_pwd},
            headers={'X-CSRFToken': csrf}
        )


    def login(self, response: HtmlResponse):
        j_body = response.json()
        if j_body.get('authenticated'):
            for parse_user in self.parse_users:
                yield response.follow(
                    f'/{parse_user}',
                    callback=self.user_data_parse,
                    cb_kwargs={'username': parse_user}
                )

    def user_data_parse(self, response: HtmlResponse, username):
        user_id = self.get_user_id(response.text, username)
        variables = {'id': user_id,
                     'first': 12}
        url_posts = f'{self.inst_graphql_link}query_hash={self.posts_hash}&{urlencode(variables)}'
        yield response.follow(url_posts,
                              callback=self.user_posts_parse,
                              cb_kwargs={'username': username,
                                         'user_id': user_id,
                                         'variables': deepcopy(variables)})

        followers_variables = {'count': 12,
                     'search_surface': 'follow_list_page'}
        url_followers = f'{self.ins_follow_link}{user_id}/followers/?{urlencode(followers_variables)}'
        yield response.follow(url_followers,
                              callback=self.user_follow_parser,
                              cb_kwargs={'username': username,
                                         'user_id': user_id,
                                         'followers_variables': deepcopy(followers_variables),
                                         'following_variables': False},
                              headers={'User-Agent': self.user_agent})

        following_variables = {'count': 12}
        url_following = f'{self.ins_follow_link}{user_id}/following/?{urlencode(following_variables)}'
        yield response.follow(url_following,
                              callback=self.user_follow_parser,
                              cb_kwargs={'username': username,
                                         'user_id': user_id,
                                         'followers_variables': False,
                                         'following_variables': deepcopy(following_variables)},
                              headers={'User-Agent': self.user_agent})

    def user_posts_parse(self, response: HtmlResponse, username, user_id, variables):
        j_data = response.json()
        page_info = j_data.get('data').get('user').get('edge_owner_to_timeline_media').get('page_info')
        if page_info.get('has_next_page'):
            variables['after'] = page_info.get('end_cursor')
            url_posts = f'{self.inst_graphql_link}query_hash={self.posts_hash}&{urlencode(variables)}'
            yield response.follow(url_posts,
                                  callback=self.user_posts_parse,
                                  cb_kwargs={'username': username,
                                             'user_id': user_id,
                                             'variables': deepcopy(variables)},
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'})
        posts = j_data.get('data').get('user').get('edge_owner_to_timeline_media').get('edges')
        for post in posts:
            item = InstaparserItem(
                user_id=user_id,
                username=username,
                post_photo_id=post.get('node').get('id'),
                post_photo=post.get('node').get('display_url'),
                post_likes=post.get('node').get('edge_media_preview_like').get('count'),
                post_data=post.get('node'),
                type_info='post'
            )
            yield item

    def user_follow_parser(self, response: HtmlResponse, username, user_id, followers_variables, following_variables):
        j_data = response.json()
        next_page = j_data.get('next_max_id')
        if followers_variables:
            info = 'followers'
        elif following_variables:
            info = 'following'

        if next_page:
            if following_variables:
                following_variables['max_id'] = int(next_page)
                url_following = f'{self.ins_follow_link}{user_id}/{info}/?{urlencode(following_variables)}'
                yield response.follow(url_following,
                                      callback=self.user_follow_parser,
                                      cb_kwargs={'username': username,
                                                 'user_id': user_id,
                                                 'followers_variables': False,
                                                 'following_variables': deepcopy(following_variables)},
                                      headers={'User-Agent': self.user_agent})
            elif followers_variables:
                followers_variables['max_id'] = next_page
                url_followers = f'{self.ins_follow_link}{user_id}/followers/?{urlencode(followers_variables)}'
                yield response.follow(url_followers,
                                      callback=self.user_follow_parser,
                                      cb_kwargs={'username': username,
                                                 'user_id': user_id,
                                                 'followers_variables': deepcopy(followers_variables),
                                                 'following_variables': False},
                                      headers={'User-Agent': self.user_agent})

        users = j_data.get('users')
        for user in users:
            item = InstaparserItem(
                user_id=user_id,
                username=username,
                type_info=info,
                f_user_id=user.get('pk'),
                f_username=user.get('username'),
                profile_photo=user.get('profile_pic_url'),
                profile_pic_id=user.get('profile_pic_id')
            )
            yield item


    def get_user_id(self, text, username):
        try:
            matched = re.search(
                '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
            ).group()
            return json.loads(matched).get('id')
        except:
            return re.findall('\"id\":\"\\d+\"', text)[-1].split('"')[-2]


    def get_token(self, text):
        """ Get csrf-token for auth """
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')
    