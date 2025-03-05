# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)

User = get_user_model()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Модель администрирования ингредиентов"""

    list_display = ('pk', 'name', 'measurement_unit',)
    list_display_links = ('pk', 'name',)
    search_fields = ('name',)
    empty_value_display = '-пусто-'


class IngredientInLine(admin.TabularInline):
    """Модель отображения ингредиентов в табличном формате"""

    model = RecipeIngredient
    fields = ('name', 'measurement_unit',)
    extra = 1


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Модель администрирования рецепта и ингредиента"""

    extra = 1

    list_display = ('recipe', 'ingredient', 'amount',)
    list_display_links = ('recipe', 'ingredient',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Модель администрирования тегов"""

    list_display = ('pk', 'name', 'slug',)
    search_fields = ('name', 'slug',)
    empty_value_display = '-пусто-'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Модель администрирования рецептов"""

    list_display = ('pk', 'author', 'name', )
    list_display_links = ('author',)
    search_fields = ('author', 'name',)
    list_filter = ('tags',)
    empty_value_display = '-пусто-'
    inlines = (IngredientInLine,)

    def get_queryset(self, request):
        """Переопределение списка рецептов в избранном"""
        queryset = super().get_queryset(request)
        return queryset.annotate(favorites_count=Count('favorites'))

    def favorites_count(self, obj):
        """Выводит общее число добавлений этого рецепта в избранное"""
        # Берём модель избраного и через queryset отбираем значение
        # с выводом количества раз
        return obj.favorites_count

    favorites_count.short_description = 'Добавлено в избранное'
    favorites_count.admin_order_field = 'favorites_count'




@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Модель администрирования избранного"""

    list_display = ('pk', 'user', 'recipe',)
    list_display_links = ('user', 'recipe',)
    search_fields = ('user',)
    list_filter = ('recipe',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Модель администрирования списка покупок"""

    list_display = ('pk', 'user', 'recipe',)
    list_display_links = ('pk', 'user', 'recipe',)
    search_fields = ('user', 'recipe',)


admin.site.site_header = 'FoodGram. Администрирование.'
