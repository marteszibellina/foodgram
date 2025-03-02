# -*- coding: utf-8 -*-
"""
Сериализаторы для приложения api, работающие с Recipes и Users

Сериализаторы заняли наиболее большой объём работы и головной боли (буквально).

@author: marteszibellina
"""

import base64
import webcolors

from djoser.serializers import UserCreateSerializer as UCS
from djoser.serializers import SetPasswordSerializer

from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model

from rest_framework import serializers, validators


from api.utils import (recipe_create,
                       check_favorite_in_list,
                       UserSubscribe)

from recipes.models import (Ingredient,
                            Tag,
                            Recipe,
                            RecipeIngredient,
                            Favorite,
                            ShoppingCart,
                            )

from recipes import constants

from users.models import Subscriptions

User = get_user_model()


class Hex2NameColor(serializers.Field):
    """Сериализатор для преобразования цвета в его название."""

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            data = webcolors.hex_to_name(data)
        except ValueError:
            raise serializers.ValidationError('Для этого цвета нет имени')
        return data


class Base64ImageField(serializers.ImageField):
    """Сериализатор для преобразования изображения в base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserViewSerializer(serializers.ModelSerializer, UserSubscribe):
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
                  'avatar',
                  )


class UserCreateSerializer(UCS, UserSubscribe):
    """Сериализатор создания пользователя."""

    class Meta:
        """Мета-класс сериализатора."""

        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'password',
                  )

    def validate(self, attrs):
        """Валидация полученных данных."""
        email = attrs.get('email')
        username = attrs.get('username')
        user_username = User.objects.filter(username=username).first()
        user_email = User.objects.filter(email=email).first()

        errors = {}
        error_template = 'Пользователь с таким {field_name} уже существует'

        field_names = ['email', 'username']
        field_values = [user_email, user_username]

        if user_email != user_username:
            errors = {
                field: [error_template.format(field_name=field)]
                for field, value in zip(field_names, field_values)
                if value
            }

            if errors:
                raise serializers.ValidationError(errors)
        return attrs


class UserPasswordSerializer(SetPasswordSerializer):
    """Сериализатор изменения пароля пользователя."""

    class Meta:
        """Мета-класс сериализатора."""

        model = User
        fields = ('current_password', 'new_password')

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                {'current_password': 'Указаный пароль не верен.'})
        return value


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор изменения аватара пользователя."""

    avatar = Base64ImageField()

    class Meta:
        """Мета-класс сериализатора."""

        model = User
        fields = ('avatar',)


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

    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    amount = serializers.IntegerField()
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit', read_only=True)


    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'amount', 'measurement_unit')


class RecipeViewSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра рецепта."""

    author = UserViewSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeIngredientViewSerializer(read_only=True, many=True, source='recipe_ingredients')
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        exclude = ('pub_date',)  # Исключаем поле с датой публикации

    def get_is_favorited(self, obj):
        """Проверка на наличие в избранном."""
        return check_favorite_in_list(self.context.get('request'), obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        """Проверка на наличие в корзине."""
        return check_favorite_in_list(self.context.get('request'), obj, ShoppingCart)


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта."""

    author = UserViewSerializer(read_only=True, default=UserViewSerializer())
    image = Base64ImageField(max_length=None, use_url=True)
    name = serializers.CharField(max_length=constants.MAX_RECIPE_NAME, required=True, allow_blank=False)
    text = serializers.CharField(max_length=constants.MAX_RECIPE_TEXT, required=True, allow_blank=False)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    ingredients = RecipeIngredientCreateSerializer(many=True, source='recipe_ingredients')
    cooking_time = serializers.IntegerField(
        min_value=constants.MIN_COOKING_TIME,
        max_value=constants.MAX_COOKING_TIME,
        error_messages={
            'min_value': constants.COOKING_TIME_ERROR,
            'max_value': constants.COOKING_TIME_ERROR,
        }
    )
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients', 'name', 'image', 'text', 'cooking_time', 'is_favorited', 'is_in_shopping_cart')
        read_only_fields = ('author',)
        validators = [
            validators.UniqueTogetherValidator(
                queryset=Recipe.objects.all(),
                fields=('name', 'author'),
                message='Рецепт с таким названием уже существует.'
            )
        ]

    def get_author(self, obj):
        """Получение автора рецепта."""
        return {
            'id': obj.author.id,
            'email': obj.author.email,
            'username': obj.author.username,
            'first_name': obj.author.first_name,
            'last_name': obj.author.last_name,
            'is_subscribed': False,
            'avatar': obj.author.avatar.url if obj.author.avatar else None,
        }

    def validate_ingredients(self, data):
        """Проверка ингредиентов на уникальность и существование."""
        ingredients = []
        for recipe_ingredient in data:
            ingredient_id = recipe_ingredient.get('id')
            if ingredient_id in ingredients:
                raise serializers.ValidationError('Ингредиенты должны быть уникальными.')
            if not ingredient_id:
                raise serializers.ValidationError('Один или несколько ингредиентов не существуют.')
            ingredients.append(ingredient_id)
        if not ingredients:
            raise serializers.ValidationError('Один или несколько ингредиентов не существуют.')
        return data

    def validate_tags(self, data):
        """Проверка на существование и уникальность тегов."""
        tags_list = [tag.id for tag in data]
        tags = Tag.objects.filter(id__in=tags_list)
        if not tags:
            raise serializers.ValidationError('Один или несколько тегов не существуют.')
        if len(tags_list) != len(set(tags_list)):
            raise serializers.ValidationError('Теги должны быть уникальными.')
        return data

    def validate_name(self, value):
        """Проверка наличия рецепта с таким же названием в базе."""
        if Recipe.objects.filter(name=value).exists():
            raise serializers.ValidationError('Рецепт с таким названием уже существует.')
        if len(value) > constants.MAX_RECIPE_NAME:
            raise serializers.ValidationError('Название рецепта слишком длинное.')
        if len(value) < constants.MIN_RECIPE_NAME:
            raise serializers.ValidationError('Название рецепта слишком короткое.')
        return value

    def create(self, validated_data):
        """Создание нового рецепта."""
        print('VALIDATA: ', validated_data)
        user = self.context['request'].user
        print('USER: ', user)
        validated_data['author'] = user
        # ingredients = validated_data.get('recipe_ingredients')
        ingredients = validated_data.pop('recipe_ingredients')
        print('INGREDIENTS: ', ingredients)
        self.validate_ingredients(ingredients)
        # tags = validated_data.get('tags')
        tags = validated_data.pop('tags')
        self.validate_tags(tags)
        self.validate_name(validated_data['name'])
        print('TAGS: ', tags)
        recipe = Recipe.objects.create(**validated_data)
        tag_serializer = TagSerializer(tags, many=True)
        for tag_data in tag_serializer.data:
            print('TAG_DATA: ', tag_data)
            tag = Tag.objects.get(id=tag_data['id'], name=tag_data['name'], slug=tag_data['slug'])
            recipe.tags.add(tag)
        # recipe.tags.set(tag)
        recipe_create(recipe, ingredients)
        # recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        tags = validated_data.get('tags')
        if tags:
            instance.tags.set(tags)
        else:
            raise serializers.ValidationError('Один или несколько тегов не существуют.')

        ingredients = validated_data.get('recipe_ingredients')
        if ingredients:
            instance.recipe_ingredients.set(ingredients)
        else:
            raise serializers.ValidationError('Один или несколько ингредиентов не существуют.')

        return super().update(instance, validated_data)


class SubscribeRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта для подписки."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscribeSerializer(serializers.ModelSerializer):
    """Сериализатор создания подписки."""

    id = serializers.IntegerField()
    email = serializers.EmailField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipe_count = serializers.IntegerField(read_only=True)
    avatar = serializers.ImageField()

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
            'recipes',
            'recipe_count',
            'avatar',
        )

    def get_recipe_count(self, obj):
        """Получение количества рецептов автора."""
        return obj.recipes.count() if obj.recipes.exists() else 0

    def get_recipes(self, obj):
        """Получение рецептов автора с учетом лимита."""
        request = self.context.get('request')
        if not request:
            return []
        recipes = obj.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except ValueError:
                pass

        return SubscribeRecipeSerializer(recipes, many=True,
                                         context={'request': request}).data

    def to_representation(self, instance):
        """Переопределяем to_representation для
        добавления recipe_count в ответ.
        """
        # Потому что другого я не придумал.
        data = super().to_representation(instance)
        data['recipe_count'] = self.get_recipe_count(instance)
        return data

    def subscribe(self, user):
        """Логика подписки на пользователя."""
        user_to_subscribe = self.instance
        if user == user_to_subscribe:
            raise serializers.ValidationError(
                {"detail": "Нельзя подписаться на самого себя."})
        subscription, created = Subscriptions.objects.get_or_create(
            user=user,
            author=user_to_subscribe)
        serialized_data = self.data
        serialized_data['is_subscribed'] = True
        return serialized_data, created


class SubscribeViewSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о подписке."""

    # Используем связанные поля через авторов подписки (user и author)
    # Надо подумать, как сделать этот и предыдущий сериализатор одним
    id = serializers.IntegerField(source='author.id')
    email = serializers.EmailField(source='author.email')
    username = serializers.CharField(source='author.username')
    first_name = serializers.CharField(source='author.first_name')
    last_name = serializers.CharField(source='author.last_name')
    is_subscribed = serializers.BooleanField(read_only=True)
    recipes = serializers.SerializerMethodField()
    recipe_count = serializers.IntegerField(read_only=True)
    avatar = serializers.ImageField(source='author.avatar')

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
            'recipe_count',
            'avatar',
            'recipes',
        )

    def get_recipes_count(self, obj):
        """Получение количества рецептов автора."""
        return obj.author.recipes.count() if obj.author.recipes.exists() else 0

    def get_recipes(self, obj):
        """Получение рецептов автора с учетом лимита."""
        request = self.context.get('request')
        if not request:
            return []

        recipes = obj.author.recipes.all()
        recipes_limit = request.query_params.get('recipes_limit')

        if recipes_limit is not None:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except ValueError:
                pass

        return SubscribeRecipeSerializer(recipes,
                                         many=True,
                                         context={'request': request}).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['recipe_count'] = self.get_recipes_count(instance)
        return data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого представления рецепта."""

    image = Base64ImageField()

    class Meta:
        """Мета-класс сериализатора."""
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор списка покупок."""

    user = UserViewSerializer(read_only=True)

    class Meta:
        """Мета-класс сериализатора."""

        model = ShoppingCart
        fields = ('user',
                  'recipe',
                  )

    def validate(self, attrs):
        """Валидация полученных данных."""
        user = self.context['request'].user
        recipe = attrs['recipe']
        print(recipe)
        if not recipe:
            raise serializers.ValidationError(
                {'detail': print(attrs)},
                'Рецепт не найден.')
        if user.shopping_cart.filter(recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в списке покупок.')
        return attrs


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор избранного."""

    class Meta:
        """Мета-класс сериализатора."""

        model = Favorite
        fields = ('user',
                  'recipe',
                  )

    def validate(self, attrs):
        """Валидация полученных данных."""
        user = self.context['request'].user
        recipe = attrs['recipe']
        if user.favorites.filter(recipe=recipe).exists():
            raise serializers.ValidationError('Рецепт уже в избранном.')
        return attrs
