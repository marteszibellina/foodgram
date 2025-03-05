# -*- coding: utf-8 -*-

from foodgram_backend import settings
from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Пагинация для списка пользователей и рецептов."""

    page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
    page_size_query_param = 'limit'
