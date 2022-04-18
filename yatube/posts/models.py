from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name=_('заголовок'),
        max_length=200
    )
    slug = models.SlugField(
        verbose_name=_('параметр ссылки'),
        max_length=50, unique=True)
    description = models.TextField(verbose_name=_('описание'),)

    class Meta:
        verbose_name = 'сообщество'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name=_('текст публикации'),
        help_text='Текст новой публикации'
    )
    pub_date = models.DateTimeField(
        verbose_name=_('дата создания'),
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        verbose_name=_('автор'),
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        verbose_name=_('сообщество'),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts'
    )
    image = models.ImageField(
        verbose_name=_('Картинка'),
        upload_to='posts/',
        blank=True
    )

    class Meta:
        verbose_name = 'публикация'
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name=_('пост'),
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name=_('автор'),
        on_delete=models.CASCADE,
        related_name='comments'
    )
    text = models.TextField(verbose_name=_('текст комментария'))
    created = models.DateTimeField(
        verbose_name=_('дата создания'),
        help_text='Текст нового комментария',
        auto_now_add=True
    )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name=_('подписчик'),
        on_delete=models.CASCADE,
        related_name='follower'
    )
    author = models.ForeignKey(
        User,
        verbose_name=_('автор подписки'),
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        verbose_name = 'подписка'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique user follow'
            )
        ]
