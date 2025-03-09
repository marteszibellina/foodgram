# -*- coding: utf-8 -*-

from rest_framework.pagination import PageNumberPagination


class StandartPagination(PageNumberPagination):
    """Пагинация для списка пользователей и рецептов."""

    page_size = 6
    page_size_query_param = 'limit'
