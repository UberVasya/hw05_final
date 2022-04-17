from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Group, Post
from django.urls import reverse
from http import HTTPStatus
from django.core.cache import cache

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='gruppen',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group
        )
        cls.all_url = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list',
                kwargs={'slug': 'gruppen'}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': 'TestUser'}
            ),
            'post_detail': reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.id}
            ),
            'post_create': reverse('posts:post_create'),
            'post_edit': reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.id}
            ),
            'login': reverse('users:login')
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_all_url_anonymous(self):
        anonymous_urls = [
            self.all_url.get('index'),
            self.all_url.get('group_list'),
            self.all_url.get('profile'),
            self.all_url.get('post_detail')
        ]
        for i in anonymous_urls:
            with self.subTest(i=i):
                response = self.guest_client.get(i)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_authorized(self):
        """Страница posts/<post_id>/edit/
        доступна авторизованному пользователю."""
        response = self.authorized_client.get(self.all_url.get('post_edit'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу posts/<post_id>/edit/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            self.all_url.get('post_edit'),
            follow=True
        )
        login_url = self.all_url.get('login')
        self.assertRedirects(
            response, f'{login_url}?next=/posts/{self.post.id}/edit/'
        )

    def test_post_create_url_authorized(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(self.all_url.get('post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            self.all_url.get('post_create'),
            follow=True
        )
        login_url = self.all_url.get('login')
        self.assertRedirects(
            response, f'{login_url}?next=/create/'
        )

    def test_unexisting_page_url_anonymous(self):
        """Страница unexisting_page не существует"""
        response = self.client.get("/unexisting_page/", follow=True)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.all_url.get('index'): 'posts/index.html',
            self.all_url.get('group_list'): 'posts/group_list.html',
            self.all_url.get('profile'): 'posts/profile.html',
            self.all_url.get('post_detail'): 'posts/post_detail.html',
            self.all_url.get('post_create'): 'posts/create_post.html',
            self.all_url.get('post_edit'): 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
