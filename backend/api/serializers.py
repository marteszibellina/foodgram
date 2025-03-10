# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers, validators

from api.fields import Base64ImageField
from api.utils import UserSubscribe
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscriptions

User = get_user_model()


class UserViewSerializer(UserSubscribe, serializers.ModelSerializer):
    """Сериализатор просмотра информации о пользователе."""

    class Meta:
        """Мета-класс сериализатора."""

        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор изменения аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        """Мета-класс сериализатора."""

        model = User
        fields = ('avatar',)

    def validate(self, attrs):
        """Валидация аватара на случай, если пустая строка."""
        avatar = attrs.get('avatar')
        if not avatar:
            raise serializers.ValidationError({'avatar': 'Обязательное поле.'})
        return attrs


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientViewSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных о рецепте и ингредиентах."""

    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    amount = serializers.IntegerField()
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        """Мета-класс сериализатора."""

        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        """Мета-класс сериализатора."""

        model = RecipeIngredient
        fields = ('id',
                  'amount',)


class RecipeViewSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра рецепта."""

    author = UserViewSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeIngredientViewSerializer(
        read_only=True,
        many=True,
        source='recipe_ingredients')
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False)

    class Meta:
        """Мета-класс сериализатора."""

        model = Recipe
        exclude = ('pub_date',)  # Всё, кроме даты публикации


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта."""

    image = Base64ImageField(max_length=None, use_url=True)
    ingredients = RecipeIngredientCreateSerializer(
        many=True, source='recipe_ingredients')
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)

    class Meta:
        """Мета-класс сериализатора."""

        model = Recipe
        fields = ('id',
                  'tags',
                  'ingredients',
                  'name',
                  'image',
                  'text',
                  'cooking_time',)

    def validate(self, data):
        """Валидация полученных данных."""
        ingredients = data.get('recipe_ingredients', [])
        if not ingredients:
            raise serializers.ValidationError(
                {'detail': 'Ингредиенты не переданы.'},
            )
        ingredients_id = set()  # Множество для быстрого поиска
        for recipe_ingredient in ingredients:
            ingredient_id = recipe_ingredient.get('id')

            if ingredient_id in ingredients_id:
                raise serializers.ValidationError(
                    {'detail': 'Ингредиенты должны быть уникальными.'}
                )
            ingredients_id.add(ingredient_id)

        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError('Теги обязательны')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги должны быть уникальными.')

        return data

    @staticmethod
    def recipe_create_update(recipe, ingredients):
        """
        Создание рецепта|Обновление рецепта.
        """
        ingredient_list = [
            RecipeIngredient(
                ingredient=ingredient['id'],
                recipe=recipe,
                amount=ingredient['amount'],
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredient_list)

    @transaction.atomic
    def create(self, validated_data):
        """Создание нового рецепта."""
        user = self.context['request'].user
        validated_data['author'] = user
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.recipe_create_update(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновление рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        instance.tags.set(tags)
        instance.ingredients.clear()  # Очистка ингредиентов
        self.recipe_create_update(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Преобразование объекта в JSON."""
        return RecipeViewSerializer(instance, context=self.context).data


class RecipeViewSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра рецепта."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class SubscribeViewSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра подписки."""

    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(default=0)
    recipes = serializers.SerializerMethodField()

    class Meta:
        """Мета-класс сериализатора."""

        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'avatar',
                  'recipes_count',
                  'recipes',)
        read_only_fields = ('id',
                            'email',
                            'username',
                            'first_name',
                            'last_name',)

    def get_is_subscribed(self, obj):
        """Проверка на наличие подписки."""
        user = self.context['request'].user
        return Subscriptions.objects.filter(author=obj, user=user).exists()

    def get_recipes(self, obj):
        """Получение рецептов."""
        request = self.context.get('request')
        recipes_limit = int(request.GET.get('recipes_limit', 0))
        return RecipeViewSubscriptionSerializer(
            Recipe.objects.filter(author=obj)[:recipes_limit],
            many=True,
            context={'request': request}).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов."""
        return obj.author.recipes.count()


class SubscribeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Subscriptions
        fields = ('user', 'author')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Subscriptions.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого автора.'),
        ]

    def validate(self, data):
        """Валидация для создания подписки."""
        user = self.context.get('request').user  # Можно достать из data
        author = data.get('author')  # Можно достать из data

        if user == author:
            raise serializers.ValidationError(
                {'detail': 'Нельзя подписаться на самого себя.'})

        return data

    def to_representation(self, instance):
        """Преобразование объекта в JSON."""
        return SubscribeViewSerializer(instance.author,
                                       context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок."""

    class Meta:
        """Мета-класс сериализатора."""

        model = ShoppingCart
        fields = ('user', 'recipe',)
        validators = [
            validators.UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в списке покупок.')]


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном.')]
