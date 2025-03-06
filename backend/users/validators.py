# -*- coding: utf-8 -*-

# import re

from django.core.exceptions import ValidationError


def validate_password(value):
    """Проверка пароля"""

    # Пароль не должен быть "password"
    if value == 'password':
        raise ValidationError('Пароль не должен быть "password"')
    # Проверка, что пароль не пустой
    if value is None or value == '':
        raise ValidationError('Пароль не может быть пустым')
    # Проверка, что пароль не менее 8 символов
    if len(value) < 8:
        raise ValidationError('Пароль должен содержать не менее 8 символов')
    return value


def selfsubscribe(self, data):
    """Проверка, что пользователь не может подписаться на себя."""
    user = data.get('user')
    author = data.get('author')
    if user == author:
        raise ValidationError('Нельзя подписаться на самого себя')
    return data
