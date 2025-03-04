# -*- coding: utf-8 -*-
"""
Фильтры для приложения api, работающие с Recipes и Users

@author: dmitry
"""

from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Фильтры для рецептов"""

    # Фильтр по автору (по id)
    author = filters.NumberFilter(
        field_name='author__id',
        # Ищем точное совпадение
        lookup_expr='exact',)
    # Фильтр по тегам (по слагу)
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),)

    class Meta:
        """Мета-класс фильтра"""

        model = Recipe
        # По умолчанию: фильтрация по избранному, автору, тегу и списку покупок
        fields = ('author',
                  'tags',
                  )


class IngredientFilter(filters.FilterSet):
    """Фильтры для ингредиентов"""

    # Фильтр по названию
    name = filters.CharFilter(
        field_name='name',
        # Ищем по началу
        lookup_expr='istartswith',)

    class Meta:
        """Мета-класс фильтра"""

        model = Ingredient
        fields = ('name',)
