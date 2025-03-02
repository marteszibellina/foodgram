# -*- coding: utf-8 -*-
"""
Пагинация для приложения api, работающая с Recipes и Users

@author: marteszibellina
"""

from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Пагинация для списка пользователей и рецептов."""

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 10
