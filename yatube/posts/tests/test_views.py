import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from ..models import Post, Group, Follow
from django.core.cache import cache


User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class TestPostPages(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.follower = User.objects.create_user(username='TestFollower')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='gruppen',
            description='Тестовое описание группы'
        )
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.test_image = SimpleUploadedFile(
            name="test.png",
            content=image,
            content_type="image/png"
        )
        cls.posts_single = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group,
            image=cls.test_image
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(
            tempfile.mkdtemp(dir=settings.BASE_DIR),
            ignore_errors=True
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.get(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'gruppen'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'TestUser'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.posts_single.id}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.posts_single.id}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.posts_single.text)
        self.assertEqual(first_object.author, self.posts_single.author)
        self.assertEqual(first_object.group, self.posts_single.group)
        self.assertEqual(first_object.image, f"posts/{self.test_image}")

    def test_index_cache(self):
        """Шаблон index кешируется."""
        response_1 = self.guest_client.get(reverse('posts:index'))
        Post.objects.create(text='test2', author=self.user)
        response_2 = self.guest_client.get(reverse('posts:index'))
        cache.clear()
        response_3 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(response_1.content, response_2.content)
        self.assertNotEqual(response_2.content, response_3.content)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'gruppen'}
        ))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.posts_single.text)
        self.assertEqual(first_object.author, self.posts_single.author)
        self.assertEqual(first_object.group, self.posts_single.group)
        self.assertEqual(first_object.image, f"posts/{self.test_image}")

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'TestUser'}
        ))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.text, self.posts_single.text)
        self.assertEqual(first_object.author, self.posts_single.author)
        self.assertEqual(first_object.group, self.posts_single.group)
        self.assertEqual(first_object.image, f"posts/{self.test_image}")

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.posts_single.id}
        ))
        first_object = response.context['post']
        self.assertEqual(first_object.text, self.posts_single.text)
        self.assertEqual(first_object.author, self.posts_single.author)
        self.assertEqual(first_object.group, self.posts_single.group)
        self.assertEqual(first_object.image, f"posts/{self.test_image}")

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.posts_single.id}
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_created_post_is_visible_on_pages(self):
        """Созанный пост доступен на сраницах: главная, группы, пользователя"""
        pages = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'gruppen'}),
            reverse('posts:profile', kwargs={'username': 'TestUser'})
        )
        for url in pages:
            response = self.authorized_client.get(url)
            with self.subTest(url=url):
                self.assertIn(
                    self.posts_single,
                    response.context['page_obj'].object_list
                )

    def test_follow_page_subscribed(self):
        """На странице follow_index есть новые посты автора из подписки"""
        Follow.objects.create(
            user=self.user,
            author=self.user
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        post_count = len(response.context['page_obj'])
        Post.objects.create(
            text='Новый тестовый пост',
            author=self.user,
            group=self.group,
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), post_count + 1)

    def test_profile_follow(self):
        """На странице profile можно подписаться на автора."""
        self.authorized_client.force_login(self.follower)
        self.authorized_client.get(reverse('posts:profile_follow', kwargs={'username': self.user}))
        self.assertTrue(Follow.objects.filter(user=self.follower, author=self.user).exists())

    def test_profile_unfollow(self):
        """На странице profile можно отписаться от автора."""
        if not Follow.objects.filter(user=self.user, author=self.user).exists():
            Follow.objects.create(user=self.user, author=self.user)
        self.authorized_client.get(reverse(
            'posts:profile_unfollow', kwargs={'username': self.user}
        ))
        self.assertFalse(Follow.objects.filter(user=self.user, author=self.user).exists())


class TestPostPagesPaginator(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='gruppen',
            description='Тестовое описание группы'
        )
        objs = (
            Post(text='Тестовый текст поста номер %s' % i,
                 author=cls.user,
                 group=cls.group
                 ) for i in range(13)
        )
        Post.objects.bulk_create(objs)

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_index_first_page_contains_ten_records(self):
        """Шаблон index сформирован пагинатор 1-я страница."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_contains_three_records(self):
        """Шаблон index сформирован пагинатор 2-я страница."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']), 3)
