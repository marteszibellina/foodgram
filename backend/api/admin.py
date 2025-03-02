# -*- coding: utf-8 -*-
"""
Администрирование всех моделей

@author: marteszibellina
"""

from django.contrib import admin
from django.contrib.auth import get_user_model

from recipes.models import (Ingredient,
                            Tag,
                            Recipe,
                            RecipeIngredient,
                            Favorite,
                            ShoppingCart,
                            )
from users.models import Subscriptions

User = get_user_model()


class UserAdmin(admin.ModelAdmin):
    """Модель администрирования пользователя"""

    list_display = ('pk',
                    'username',
                    'email',
                    'first_name',
                    'last_name',
                    'date_joined'
                    )
    list_display_links = ('pk', 'username', 'email',)
    search_fields = ('username', 'email',)
    list_filter = ('username', 'email',)
    empty_value_display = '-пусто-'


class SubsriptionsAdmin(admin.ModelAdmin):
    """Модель администрирования подписок"""

    list_display = ('pk', 'user', 'author',)
    list_display_links = ('user', 'author',)
    search_fields = ('user', 'author',)
    list_filter = ('user',)


class IngredientAdmin(admin.ModelAdmin):
    """Модель администрирования ингредиентов"""

    list_display = ('pk', 'name', 'measurement_unit',)
    list_display_links = ('pk', 'name',)
    search_fields = ('name',)
    empty_value_display = '-пусто-'


# Есть ли смысл?
class IngredientInLine(admin.TabularInline):
    """Модель отображения ингредиентов в табличном формате"""

    model = Ingredient
    fields = ('name', 'measurement_unit',)


class TagAdmin(admin.ModelAdmin):
    """Модель администрирования тегов"""

    list_display = ('pk', 'name', 'slug',)
    search_fields = ('name', 'slug',)
    empty_value_display = '-пусто-'


class RecipeAdmin(admin.ModelAdmin):
    """Модель администрирования рецептов"""

    list_display = ('pk', 'author', 'name', )
    list_display_links = ('author',)
    search_fields = ('author', 'name',)
    list_filter = ('tags',)
    empty_value_display = '-пусто-'

    def favorites_count(self, obj):
        """Выводит общее число добавлений этого рецепта в избранное"""
        # Берём модель избраного и через queryset отбираем значение
        # с выводом количества раз
        return Favorite.objects.filter(recipe=obj).count()


class RecipeIngredientAdmin(admin.ModelAdmin):
    """Модель администрирования рецепта и ингредиента"""

    list_display = ('recipe', 'ingredient', 'amount',)
    list_display_links = ('recipe', 'ingredient',)


class FavoriteAdmin(admin.ModelAdmin):
    """Модель администрирования избранного"""

    list_display = ('pk', 'user', 'recipe',)
    list_display_links = ('user', 'recipe',)
    search_fields = ('user',)
    list_filter = ('recipe',)


class ShoppingCartAdmin(admin.ModelAdmin):
    """Модель администрирования списка покупок"""

    list_display = ('pk', 'user', 'recipe',)
    list_display_links = ('pk', 'user', 'recipe',)
    search_fields = ('user', 'recipe',)


admin.site.register(User, UserAdmin)
admin.site.register(Subscriptions, SubsriptionsAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(RecipeIngredient, RecipeIngredientAdmin)
admin.site.register(Favorite, FavoriteAdmin)
admin.site.register(ShoppingCart, ShoppingCartAdmin)

admin.site.site_header = 'FoodGram. Администрирование.'
