# -*- coding: utf-8 -*-
"""
Модель пользователя.

@author: marteszibellina
"""

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from users.constants import (USERNAME_MAX_LENGTH, EMAIL_MAX_LENGTH,
                             FIRST_NAME_MAX_LENGTH, LAST_NAME_MAX_LENGTH,
                             PASSWORD_MAX_LENGTH,)
from users.validators import (validate_username,
                              validate_password,
                              selfsubscribe)


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
        validators=[validate_username],
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
    password = models.CharField(
        verbose_name='Пароль',
        max_length=PASSWORD_MAX_LENGTH,
        validators=[validate_password],
        blank=False,
        help_text='Укажите Ваш пароль'
    )
    avatar = models.ImageField(
        verbose_name='Аватар',
        upload_to='users/',
        blank=True,
    )
    date_joined = models.DateField(
        verbose_name='Дата регистрации',
        default=timezone.now,
    )

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'password']

    class Meta:
        """Мета-класс модели."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Возвращает имя, фамилию и никнейм пользователя."""
        return (
            f'Пользователь:{self.first_name} {self.last_name}'
            f'({self.username})')

    # Метод для генерации кода подтверждения
    @property
    def generate_confirmation_code(self):
        """Метод для генерации кода подтверждения
        через default_token_generator."""
        return default_token_generator.make_token(self)

    def check_confirmation_code(self, code):
        """Метод для проверки кода подтверждения
        через default_token_generator."""
        return default_token_generator.check_token(self, code)


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
        # НАСТРОИТЬ
        validators=[selfsubscribe],
    )

    class Meta:
        """Мета-класс модели."""

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        """Возвращает имя, фамилию и никнейм пользователя."""
        return f'{self.user} подписан на {self.author}'

    def clean(self):
        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя!')
        return super().clean()
