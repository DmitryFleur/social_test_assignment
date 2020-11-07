import names
import requests
import json
from random import randint
from social_network.bot.config import NUM_OF_USERS, MAX_LIKES_PER_USER, MAX_POSTS_PER_USER

BASE_URL = 'http://127.0.0.1:8000/api/'


class Bot(object):
    def __init__(self):
        self.users = dict()
        self.posts = dict()
        self.likes = dict()

    def create_users(self):
        for i in range(NUM_OF_USERS):
            name = names.get_first_name().lower() + str(i)
            data = {'username': 'user_' + name,
                    'email': name + '@email.com',
                    'password': 'some_password',
                    'confirm_password': 'some_password'}
            requests.post(BASE_URL + 'sign-up/', json=data)
            data['headers'] = {'content-type': 'application/json',
                               'Authorization': 'JWT ' + self.get_user_jwt_token(data['username'],
                                                                                 data['password'])}
            data['num_of_posts'] = 0
            data['num_of_likes'] = 0
            self.users[data['username']] = data

    @staticmethod
    def get_user_jwt_token(username, password):
        r = requests.post(BASE_URL + 'token-auth/', json={'username': username,
                                                          'password': password})
        json_r = json.loads(r.content)
        return json_r['token']

    def create_posts(self):
        for user in self.users:
            for _ in range(randint(0, MAX_POSTS_PER_USER)):
                status = 'Today was a really great day. Thank you, %s' % names.get_full_name()
                r = requests.post(BASE_URL + 'post/',
                                  json={'text': status},
                                  headers=self.users[user]['headers'])
                json_r = json.loads(r.content)
                self.users[user]['num_of_posts'] += 1
                self.posts[user] = list()
                self.posts[user].append({'text': status,
                                         'likes': 0,
                                         'id': json_r['id'],
                                         'liked_by': list()})

    def create_likes(self):
        while True:
            user = self.get_applicable_user()
            user_to_like = self.get_user_with_no_likes(user)
            if not user_to_like:
                break

            random_key = randint(0, len(self.posts[user_to_like]) - 1)
            random_post = self.posts[user_to_like][random_key]
            requests.get(
                BASE_URL + 'post/%s/like_unlike/' % random_post['id'],
                headers=self.users[user]['headers'])
            self.users[user]['num_of_likes'] += 1
            self.posts[user_to_like][random_key]['likes'] += 1
            self.posts[user_to_like][random_key]['liked_by'].append(user)

    def get_applicable_user(self):
        return max(self.users, key=lambda i: self.users[i]['num_of_posts']
                   and self.users[i]['num_of_likes'] != MAX_LIKES_PER_USER)

    def get_user_with_no_likes(self, cur_user):
        for user in self.posts:
            if user != cur_user:
                for post in self.posts[user]:
                    if post['likes'] == 0 and cur_user not in post['liked_by']:
                        return user
        return None

    def run(self):
        self.create_users()
        self.create_posts()
        self.create_likes()
        print('Process has been finished')


if __name__ == "__main__":
    bot = Bot()
    bot.run()
