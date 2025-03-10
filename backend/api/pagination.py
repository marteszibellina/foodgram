# -*- coding: utf-8 -*-

from rest_framework.pagination import PageNumberPagination

from foodgram_backend.settings import PAGE_SIZE


class StandartPagination(PageNumberPagination):
    """Пагинация для списка пользователей и рецептов."""

    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
