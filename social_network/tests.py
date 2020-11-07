import json

from rest_framework.test import APITestCase
from social_network.models import UserProfile, Post, PostLike

BASE_URL = 'http://127.0.0.1:8000/api/'


class TestSocialEndpoints(APITestCase):

    token = ''

    def setUp(self):
        self.user = self._create_test_user(
            'some_username', 'some_email@email.com', 'some_password')
        self.post = Post.objects.create(
            text='I am testing a post creation..',
            user=self.user)

        response = self.client.post(
            BASE_URL + 'token-auth/',
            {'username': 'some_username', 'password': 'some_password'},
            format='json')
        resp = json.loads(response.content)
        self.token = resp['token']

    @staticmethod
    def _create_test_user(username, email, password):
        return UserProfile.objects.create_user(
            username=username,
            email=email,
            password=password
        )

    def test_sign_up(self):
        data = {
            'username': 'some_username2',
            'email': 'some_email2@email.com',
            'password': 'some_password',
            'confirm_password': 'some_password'
        }

        response = self.client.post(BASE_URL + 'sign-up/', data, format='json')
        resp = json.loads(response.content)

        self.assertEqual(resp['username'], data['username'])
        self.assertEqual(resp['email'], data['email'])
        self.assertEqual(UserProfile.objects.get(username=data['username']).username, 'some_username2')
        self.assertEqual(UserProfile.objects.get(email=data['email']).email, 'some_email2@email.com')

    def test_sign_up_with_wrong_pass_confirmation(self):
        data = {
            'username': 'some_username2',
            'email': 'some_email2@email.com',
            'password': 'some_password',
            'confirm_password': 'ololo'
        }

        response = self.client.post(BASE_URL + 'sign-up/', data, format='json')
        resp = json.loads(response.content)
        self.assertEqual(resp['non_field_errors'], ['Passwords are not the same'])

    def test_user_list_without_doing_login(self):
        url = BASE_URL + 'user/'
        response = self.client.get(url)
        resp = json.loads(response.content)
        self.assertEqual(resp['detail'], 'Authentication credentials were not provided.')

    def test_user_list(self):
        url = BASE_URL + 'user/'
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.token)
        response = self.client.get(url)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['results']), 1)

    def test_user_page(self):
        url = BASE_URL + 'user/1/'
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.token)
        response = self.client.get(url)
        resp = json.loads(response.content)
        self.assertEqual(resp['id'], 1)
        self.assertEqual(resp['username'], 'some_username')

    def test_post_like(self):
        url = BASE_URL + 'post/1/like_unlike/'
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.token)
        response = self.client.get(url)
        resp = json.loads(response.content)
        self.assertEqual(resp['message'], 'Post was successfully liked')

        post = Post.objects.get(id=1)
        likes = PostLike.objects.filter(post=post)
        self.assertEqual(len(likes), 1)

    def test_post_unlike(self):
        post = Post.objects.get(id=1)
        PostLike.objects.create(post=post, user=self.user)

        likes_before_request = PostLike.objects.filter(post=post)
        self.assertEqual(len(likes_before_request), 1)

        url = BASE_URL + 'post/1/like_unlike/'
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.token)
        response = self.client.get(url)
        resp = json.loads(response.content)
        self.assertEqual(resp['message'], 'Post was successfully unliked')
        likes_after_request = PostLike.objects.filter(post=post)
        self.assertEqual(len(likes_after_request), 0)

    def test_post_creation(self):
        posts = Post.objects.all()
        assert len(posts) == 1

        url = BASE_URL + 'post/'
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.token)
        self.client.post(url, {'text': 'Another weird post'}, format='json')

        posts = Post.objects.all()
        self.assertEqual(len(posts), 2)

    def test_posts_list(self):
        url = BASE_URL + 'post/'
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.token)
        response = self.client.get(url)
        resp = json.loads(response.content)
        self.assertEqual(len(resp['results']), 1)

    def test_post_list_without_doing_login(self):
        url = BASE_URL + 'post/'
        response = self.client.get(url)
        resp = json.loads(response.content)
        self.assertEqual(resp['detail'], 'Authentication credentials were not provided.')

    def test_likes_analytics(self):

        post = Post.objects.get(id=1)
        PostLike.objects.create(post=post, user=self.user, like_datetime='2020-06-29 08:15:27+00:00')

        second_user = self._create_test_user('username2', 'somee@mail.ru', '111')
        PostLike.objects.create(post=post, user=second_user, like_datetime='2020-06-29 08:15:27+00:00')

        third_user = self._create_test_user('username3', 'somee@mail.ru', '111')
        PostLike.objects.create(post=post, user=third_user, like_datetime='2020-04-29 08:15:27+00:00')

        url = BASE_URL + 'analytics/?date_from=2020-02-02&date_to=2020-12-31'
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.token)
        response = self.client.get(url)
        resp = json.loads(response.content)

        self.assertEqual(len(resp['results']), 2)

        for item in resp['results']:
            if item['like_datetime'] == '2020-04-29':
                self.assertEqual(item['created_count'], 1)
            elif item['like_datetime'] == '2020-06-29':
                self.assertEqual(item['created_count'], 2)

    def test_user_activity_last_request(self):
        time_before_request = self.user.last_request_datetime
        url = BASE_URL + 'post/'
        self.client.credentials(HTTP_AUTHORIZATION='JWT ' + self.token)
        self.client.get(url)
        user_profile_after_request = UserProfile.objects.get(email=self.user.email)

        self.assertNotEqual(
            user_profile_after_request.last_request_datetime,
            time_before_request
        )

    def test_user_activity_last_login(self):
        time_before_request = UserProfile.objects.get(email=self.user.email).last_login_datetime

        self.client.post(BASE_URL + 'login/', {'username': self.user.username, 'password': 'some_password'})
        user_profile_after_request = UserProfile.objects.get(email=self.user.email)

        self.assertNotEqual(
            user_profile_after_request.last_login_datetime,
            time_before_request
        )
