# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from recipes.constants import (COOKING_TIME_ERROR, INGREDIENT_AMOUNT_ERROR,
                               MAX_COOKING_TIME, MAX_INGRED_MEASURE_LENGTH,
                               MAX_INGRED_NAME_LENGTH, MAX_INGREDIENT_AMOUNT,
                               MAX_RECIPE_NAME, MAX_TAG_NAME_LENGTH,
                               MAX_TAG_SLUG_LENGTH, MIN_COOKING_TIME,
                               MIN_INGREDIENT_AMOUNT, TEXT_SLICE)
from recipes.querysets import RecipeQuerySet

User = get_user_model()


class Ingredient(models.Model):
    """Модель ингредиента."""

    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=MAX_INGRED_NAME_LENGTH,
        unique=True,
    )
    measurement_unit = models.CharField(
        verbose_name='Единица измерения',
        max_length=MAX_INGRED_MEASURE_LENGTH,
    )

    class Meta:
        """Мета-класс модели."""

        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient',
            ),
        ]

    def __str__(self):
        """Возвращает название ингредиента."""
        return self.name[:TEXT_SLICE]


class Tag(models.Model):
    """Модель тега."""

    name = models.CharField(
        verbose_name='Название тега',
        max_length=MAX_TAG_NAME_LENGTH,
        unique=True,
    )
    slug = models.SlugField(
        verbose_name='Slug тега',
        max_length=MAX_TAG_SLUG_LENGTH,
        unique=True,
    )

    class Meta:
        """Мета-класс модели."""

        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        """Возвращает название тега."""
        return self.name[:TEXT_SLICE]


class Recipe(models.Model):
    """Модель рецепта"""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта'
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME,
        verbose_name='Название рецепта',
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='images/recipes',
        help_text='Картинка готового блюда',
    )
    text = models.TextField(
        verbose_name='Текст рецепта',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Тег',
        related_name='recipes',
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[
            MinValueValidator(MIN_COOKING_TIME, message=COOKING_TIME_ERROR),
            MaxValueValidator(MAX_COOKING_TIME, message=COOKING_TIME_ERROR)])
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )

    objects = RecipeQuerySet.as_manager()  # Добавляем кверисет

    class Meta:
        """Мета-класс модели"""

        ordering = ('-pub_date',)  # Публикации с новых
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            # Проверка уникальности рецепта на уровне БД
            # на случай, если у автора такой рецепт уже есть
            # или есть такое же название
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='unique_author_recipe'),
        ]

    def __str__(self):
        """Возвращает название рецепта"""
        return self.name[:TEXT_SLICE]


class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингредиента."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipe_ingredients',
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT,
                                      message=INGREDIENT_AMOUNT_ERROR),
                    MaxValueValidator(MAX_INGREDIENT_AMOUNT,
                                      message=INGREDIENT_AMOUNT_ERROR)])

    class Meta:
        """Мета-класс модели."""

        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        constraints = [
            # Проверка уникальности ингредиента в рецепте на уровне БД
            # на случей, если в рецепте два ингредиента с одинаковым названием
            # и единицей измерения
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient',
            )
        ]

    def __str__(self):
        """Возвращает название ингредиентов в рецепте"""
        return f'В {self.recipe}: {self.ingredient},{self.amount}'


class BaseFavotireShoppingCart(models.Model):
    """Базовая абстрактная модель для избранного и списка покупок."""

    user = models.ForeignKey(
        User,
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
        related_name='%(class)s',  # user.favorites user.shopping_cart
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
        related_name='%(class)s',  # recipe.favorites recipe.shopping_cart
    )

    class Meta:
        """Мета-класс модели."""

        abstract = True
        constraints = [
            models.UniqueConstraint(
                # Проверка уникальности избранного рецепта на уровне БД
                # на случай, есди пользователь решит добавить один и тот же
                # рецепт дважды
                fields=('user', 'recipe'),
                name='%(class)s_unique_user_recipe'
            )
        ]


class Favorite(BaseFavotireShoppingCart):
    """Модель избранного"""

    class Meta(BaseFavotireShoppingCart.Meta):
        """Мета-класс модели"""

        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def __str__(self):
        """Возвращает название избранного рецепта пользователя"""
        return f'Рецепт от {self.user}: {self.recipe}'


class ShoppingCart(BaseFavotireShoppingCart):
    """Модель списка покупок"""

    class Meta(BaseFavotireShoppingCart.Meta):
        """Мета-класс модели"""

        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        """Возвращает название списка покупок пользователя"""
        return f'У {self.user} в списке: {self.recipe}'
