from ..forms import PostForm, CommentForm
from ..models import Post, Group, Comment
from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404


User = get_user_model()


class TestForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='gruppen',
            description='Тестовое описание группы'
        )
        cls.posts_single = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group
        )
        cls.form = PostForm()
        cls.form_comment = CommentForm

    def setUp(self):
        self.user = User.objects.get(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Форма на странице posts:post_create создает пост"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый новый пост',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        path = reverse('posts:profile',
                       kwargs={'username': self.user.username})
        self.assertRedirects(response, path)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.all().order_by('pk').last()
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.group, self.group)

    def test_edit_post(self):
        """Форма на странице posts:post_edit редактирует пост"""
        path = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.posts_single.pk}
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Изменили текст поста',
            'group': self.group.pk
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.posts_single.pk}
            ),
            data=form_data,
            follow=True
        )
        edited_post = get_object_or_404(Post, pk=self.posts_single.pk)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, path)
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group, self.group)

    def test_comment_create(self):
        """Форма на странице posts:post_edit создает комментарий"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий из теста',
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.posts_single.id}
            ),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.first()
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.posts_single)
