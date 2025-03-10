# -*- coding: utf-8 -*-

from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Фильтры для рецептов"""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),)
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart', label='В списке покупок')
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited', label='В избранном')

    class Meta:
        """Мета-класс фильтра"""

        model = Recipe
        # По умолчанию: фильтрация по избранному, автору, тегу и списку покупок
        fields = ('author',
                  'tags',
                  'is_favorited',
                  'is_in_shopping_cart')

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
