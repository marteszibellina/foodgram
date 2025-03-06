# -*- coding: utf-8 -*-

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

    # Фильтры по избранному
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited',
        label='В избранном',)

    # Фильтры по списку покупок
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        label='В списке покупок',)

    class Meta:
        """Мета-класс фильтра"""

        model = Recipe
        # По умолчанию: фильтрация по избранному, автору, тегу и списку покупок
        fields = ('author',
                  'tags',)

    def filter_is_favorited(self, queryset, name, value):
        """Фильтр по избранному"""
        if value:
            return queryset.filter(favorite__isnull=False).distinct()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтр по списку покупок"""
        if value:
            return queryset.filter(shoppingcart__isnull=False).distinct()
        return queryset


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
