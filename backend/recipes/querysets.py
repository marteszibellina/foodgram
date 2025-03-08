# -*- coding: utf-8 -*-

from django.db.models import QuerySet, Exists, OuterRef


class RecipeQuerySet(QuerySet):
    """Кверисет для получения списка рецептов."""

    def with_favorites_and_shopping_cart(self, user):
        """Добавление полей в кверисет."""

        # Отложенный импорт воизбежание циклического импорта
        from recipes.models import Favorite, ShoppingCart

        return self.annotate(
            is_favorited=Exists(Favorite.objects.filter(
                user=user, recipe_id=OuterRef('pk')
            )),
            is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                user=user, recipe_id=OuterRef('pk')
            ))
        )
