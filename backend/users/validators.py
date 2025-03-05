# -*- coding: utf-8 -*-

# import re

from django.core.exceptions import ValidationError

# RESTRICTED_USERNAMES = ['username', 'login', 'user', 'admin', 'me']

# Пока оставил на случай, если где-то что-то сломается и я забуду, что именно
# я сломал и как это работало раньше
# def validate_username(value):
#     """Проверка username"""

#     # Проверка, что имя пользователя не пустое
#     if value is None:
#         raise ValidationError('Имя пользователя не может быть пустым')
#     # Проверка, что имя пользователя не что-то базовое.
#     # Мы не в фильме с Лесли Нильсеном ("Wrongfully Accused, 1998")
#     if value.lower() in RESTRICTED_USERNAMES:
#         raise ValidationError(f'Имя пользователя не должно быть "{value}"')
#     # Проверка, что имя пользователя не содержит недопустимые символы
#     match = re.match(r'^[\w.@+-]+$', value)
#     if not match:
#         raise ValidationError(
#             'Имя пользователя может содержать только буквы, цифры, @, ., +, -')
#     # Проверка, что имя пользователя не менее 6 символов
#     if value.lower() not in RESTRICTED_USERNAMES and len(value) < 6:
#         raise ValidationError(
#             'Имя пользователя должно содержать не менее 6 символов')
#     return value


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
