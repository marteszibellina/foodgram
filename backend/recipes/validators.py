# -*- coding: utf-8 -*-
"""
Валидаторы для модели рецептов.

@author: marteszibelina
"""

import re

from django.core.exceptions import ValidationError


def validate_tag_slug(value):
    """Проверка slug тега."""

    match = re.match(r'^[-a-zA-Z0-9_]+$', value)
    if not match:
        raise ValidationError(
            'Slug тега может содержать только буквы, цифры, _ и -')
    if len(value) < 5:
        raise ValidationError(
            'Slug тега должен содержать не менее 5 символов')
