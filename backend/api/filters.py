# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Фильтры для рецептов"""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),)
    is_in_shopping_cart = filters.BooleanFilter(label='В списке покупок')
    is_favorited = filters.BooleanFilter(label='В избранном')

    class Meta:
        """Мета-класс фильтра"""

        model = Recipe
        # По умолчанию: фильтрация по избранному, автору, тегу и списку покупок
        fields = ('author',
                  'tags',
                  'is_favorited',
                  'is_in_shopping_cart')


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
