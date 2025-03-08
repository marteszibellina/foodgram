# -*- coding: utf-8 -*-

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models

from users.constants import (EMAIL_MAX_LENGTH, FIRST_NAME_MAX_LENGTH,
                             LAST_NAME_MAX_LENGTH, USERNAME_MAX_LENGTH)
# from users.validators import selfsubscribe


class User(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField(
        verbose_name='Адрес почты',
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        help_text='Укажите адрес Вашей электронной почты.'
    )
    username = models.CharField(
        verbose_name='Имя пользователя (никнейм)',
        max_length=USERNAME_MAX_LENGTH,
        validators=[UnicodeUsernameValidator()],
        unique=True,
        help_text='Укажите Ваш никнейм'
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=FIRST_NAME_MAX_LENGTH,
        blank=False,
        help_text='Укажите Ваше имя'
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=LAST_NAME_MAX_LENGTH,
        blank=False,
        help_text='Укажите Вашу фамилию'
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/',
        blank=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        """Мета-класс модели."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Возвращает имя, фамилию и никнейм пользователя."""
        return (
            f'(Пользователь:{self.first_name} {self.last_name} '
            f'({self.username})')


class Subscriptions(models.Model):
    """Модель подписок пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор рецептов',
        # validators=[selfsubscribe],
    )

    class Meta:
        """Мета-класс модели."""

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='subscription_prevent_self_subscription'
            )
        ]

    def __str__(self):
        """Возвращает имя, фамилию и никнейм пользователя."""
        return f'{self.user} подписан на {self.author}'

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя!')
        return super().clean()
