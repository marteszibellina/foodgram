# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model
from django.db import transaction

# from djoser.serializers import SetPasswordSerializer
# from djoser.serializers import UserCreateSerializer as UCS
from recipes import constants
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers, validators


from api.fields import Base64ImageField
from api.utils import UserSubscribe
from users.models import Subscriptions

User = get_user_model()


class UserViewSerializer(UserSubscribe, serializers.ModelSerializer):
    """Сериализатор просмотра информации о пользователе."""

    class Meta:
        """Мета-класс сериализатора."""

        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'avatar',)


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор изменения аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        """Мета-класс сериализатора."""

        model = User
        fields = ('avatar',)

    def validate_avatar(self, value):
        """Валидация аватара на случай, если пустая строка."""
        if not value:
            raise serializers.ValidationError('Поле не может быть пустым.')
        return value


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
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeViewSerializer(serializers.ModelSerializer):
    """Сериализатор просмотра рецепта."""

    author = UserViewSerializer(
        read_only=True,
    )
    tags = TagSerializer(
        read_only=True,
        many=True,
    )
    ingredients = RecipeIngredientViewSerializer(
        read_only=True,
        many=True,
        source='recipe_ingredients',
    )
    is_favorited = serializers.BooleanField(source='is_favorited',
                                            read_only=True)
    is_in_shopping_cart = serializers.BooleanField(
        source='is_in_shopping_cart', read_only=True)

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
        queryset=Tag.objects.all(),
        many=True)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False)

    class Meta:
        """Мета-класс сериализатора."""
        model = Recipe
        fields = ('id',
                  'tags',
                  'author',
                  'ingredients',
                  'name',
                  'image',
                  'text',
                  'cooking_time',
                  'is_favorited',
                  'is_in_shopping_cart')
        read_only_fields = ('author',)
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=('name', 'author'),
                message='Рецепт с таким названием уже существует.'
            )
        ]

    def validate(self, data):
        """Валидация полученных данных."""
        ingredients = data.get('recipe_ingredients', [])
        if not ingredients:
            raise serializers.ValidationError(
                {'detail:': 'Ингредиенты не переданы.'},
            )
        ingredients_id = set()  # Множество для быстрого поиска
        for recipe_ingredient in ingredients:
            ingredient_id = recipe_ingredient.get('id')

            if ingredient_id in ingredients_id:
                raise serializers.ValidationError(
                    {'detail': 'Ингредиенты должны быть уникальными.'})
            ingredients_id.add(ingredient_id)

        tags = data.get('tags', [])
        if not tags:
            raise serializers.ValidationError('Теги обязательны')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги должны быть уникальными.')

        return data

    @staticmethod
    def recipe_create(recipe, ingredients):
        """Создание рецепта"""
        ingredient_list = [RecipeIngredient(
            ingredient=ingredient['id'],
            recipe=recipe,
            amount=ingredient['amount'],
        )
            for ingredient in ingredients]
        return RecipeIngredient.objects.bulk_create(ingredient_list)

    @transaction.atomic
    def create(self, validated_data):
        """
        Создание нового рецепта.
        Если на одном из этапов возникнет ошибка, то все операции отменятся.
        """
        user = self.context['request'].user
        validated_data['author'] = user
        ingredients = validated_data.pop('recipe_ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.recipe_create(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe_ingredients')
        if tags:
            instance.tags.set(tags)
        if ingredients:
            self.recipe_create(instance, ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Преобразование объекта в JSON."""
        data = super().to_representation(instance)
        data['author'] = UserViewSerializer(instance.author).data
        return RecipeViewSerializer(instance, context=self.context).data


class RecipeViewSubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра рецепта."""

    class Meta:
        """Мета-класс сериализатора."""
        model = Recipe
        fields = (
            'id',
            'name',
            'cooking_time',
            'image',)

    def get_is_favorited(self, obj):
        """Проверка на наличие в избранном."""
        return check_favorite_in_list(
            self.context.get('request'), obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Проверка на наличие в корзине."""
        return check_favorite_in_list(
            self.context.get('request'), obj, ShoppingCart)


class SubscribeRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта для подписки."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeViewSerializer(UserViewSerializer):
    """Сериализатор просмотра подписки."""

    is_subscribed = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()

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
            'recipes_count',
            'recipes',
        )

    def get_is_subscribed(self, obj):
        """Проверка на наличие подписки."""
        user = self.context['request'].user
        return Subscriptions.objects.filter(user=user,
                                            author=obj.author).exists()

    def get_recipes(self, obj):
        """Получение рецептов."""
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit', None)
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
            except ValueError:
                recipes_limit = None
        recipes = obj.recipes.all()[:recipes_limit]
        return RecipeViewSubscriptionSerializer(recipes, many=True,
                                                context=self.context).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов."""
        return obj.recipes.count()

class SubscribeCreateSerializer(serializers.Serializer):
    """Сериализатор для создания подписки."""
    
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    author = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def validate(self, attrs):
        """Валидация для создания подписки."""
        user = self.context['request'].user
        author = attrs.get('author')

        if user == author:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя.")

        # Проверяем, существует ли уже подписка
        if Subscriptions.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого автора.")

        return attrs

    def create(self, validated_data):
        """Создание подписки."""
        user = self.context['request'].user
        author = validated_data.get('author')

        subscription = Subscriptions.objects.create(user=user, author=author)
        return subscription


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта."""

    image = Base64ImageField()

    class Meta:
        """Мета-класс сериализатора."""
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок."""

    class Meta:
        """Мета-класс сериализатора."""

        model = ShoppingCart
        fields = ('user', 'recipe',)
        constriants = validators.UniqueTogetherValidator(
            queryset=ShoppingCart.objects.all(),
            fields=('user', 'recipe'),
            message='Рецепт уже в списке покупок.')

    def validate(self, attrs):
        """Валидация полученных данных."""
        user = self.context['request'].user
        recipe = attrs['recipe']
        if not recipe:
            raise serializers.ValidationError(
                {'detail': 'Рецепт не найден.'})
        attrs['user'] = user
        return attrs


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Favorite
        fields = ('user', 'recipe',)
        validators = [validators.UniqueTogetherValidator(
            queryset=Favorite.objects.all(),
            fields=('user', 'recipe'),
            message='Рецепт уже в избранном.'
        )]
