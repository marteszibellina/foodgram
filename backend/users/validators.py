# -*- coding: utf-8 -*-

# import re

from django.core.exceptions import ValidationError


def selfsubscribe(self, data):
    """Проверка, что пользователь не может подписаться на себя."""
    user = data.get('user')
    author = data.get('author')
    if user == author:
        raise ValidationError('Нельзя подписаться на самого себя')
    return data
