# -*- coding: utf-8 -*-

from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as UVS
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import StandartPagination
from api.permissions import (IsAuthorOrReadOnly,)
from api.serializers import (FavoriteSerializer,
                             IngredientSerializer,
                             RecipeCreateSerializer,
                             ShoppingCartSerializer,
                             SubscribeCreateSerializer,
                             SubscribeViewSerializer,
                             TagSerializer,
                             RecipeViewSubscriptionSerializer,
                             UserAvatarSerializer,
                             UserViewSerializer,
                             )
from api.utils import create_list_txt, create_short_link
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscriptions

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filterset_class = IngredientFilter


class UserViewSet(UVS):
    """Вьюсет для пользователей."""

    queryset = User.objects.all()
    permission_class = (permissions.AllowAny, )
    pagination_class = StandartPagination

    def get_permissions(self):
        if self.action in ('get', 'list', 'retrieve'):
            return [permissions.AllowAny()]
        return super().get_permissions()

    @action(detail=False,
            methods=['get'],
            url_path='me',
            permission_class=[permissions.IsAuthenticated])
    def me(self, request):
        """Получение информации о текущем пользователе."""
        serializer = UserViewSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False,
            methods=['put'],
            url_path='me/avatar',
            permission_classes=(permissions.IsAuthenticated,))
    def set_avatar(self, request):
        """Смена или добавление аватара."""
        user = get_object_or_404(User, id=request.user.id)
        serializer = UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара."""
        if request.user.avatar:
            request.user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True,
            methods=['post', ],
            url_path='subscribe',
            permission_classes=[permissions.IsAuthenticated],
            pagination_class=StandartPagination)
    def subscribe(self, request, id):
        """Подписка на пользователя."""
        author = get_object_or_404(User, id=id)
        user = self.request.user
        serializer = SubscribeCreateSerializer(
            context={'request': request},
            data={'author': author.id, 'user': user.id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = SubscribeViewSerializer(User.objects.annotate(
            recipes_count=Count('recipes'),).filter(id=id).first(),
            context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        """Отписка от пользователя."""
        author = self.get_object()
        user = request.user
        subscribe, deleted = Subscriptions.objects.filter(
            user=user, author=author).delete()
        if subscribe:
            return Response(
                {'detail': 'Вы отписались от этого автора'},
                status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Вы не были подписаны на этого автора'},
            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False,
            methods=['get'],
            url_path='subscriptions',
            permission_classes=[permissions.IsAuthenticated],
            pagination_class=StandartPagination)
    def subscriptions(self, request):
        """Получение списка подписок."""
        user = request.user
        queryset = User.objects.filter(
            following__user=user).annotate(
                recipes_count=Count('recipes')).order_by('-recipes_count')  #
        pages = self.paginate_queryset(queryset)
        serializer = SubscribeViewSerializer(
            pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""

    serializer_class = RecipeCreateSerializer
    filterset_class = RecipeFilter
    pagination_class = StandartPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsAuthorOrReadOnly,)

    def get_queryset(self):
        """Получение списка рецептов."""
        queryset = Recipe.objects.all()
        if self.request.user.is_anonymous:
            return queryset
        return queryset.with_favorites_and_shopping_cart(self.request.user)

    def get_serializer_class(self):
        """Получение сериализатора."""
        if self.request.method in ['post', 'update', ]:
            return RecipeCreateSerializer
        return self.serializer_class

    @action(methods=['get'],
            detail=True,
            url_path='get-link')
    def get_link(self, request, pk=None):
        """Получение ссылки на рецепт."""
        try:
            recipe = self.get_object()
            link = create_short_link(recipe.id, request)
            return Response({'short-link': link}, status=status.HTTP_200_OK)
        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Рецепт не найден.'},
                status=status.HTTP_404_NOT_FOUND)

    def get_recipe(self, request, pk=None):
        """Получение рецепта."""
        return get_object_or_404(Recipe, id=pk)

    def handle_add(self, serializer_class, model, user, pk):
        """Добавление рецепта: избранное, список покупок."""
        recipe = self.get_recipe(self.request, pk)
        serializer = serializer_class(
            data={'user': user.id, 'recipe': recipe.id},
            context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user=self.request.user)

        recipe_serializer = RecipeViewSubscriptionSerializer(instance.recipe)
        return Response(recipe_serializer.data,
                        status=status.HTTP_201_CREATED)

    def handle_remove(self, serializer_class, model, user, pk):
        """Удаление рецепта: избранное, список покупок."""
        recipe = self.get_recipe(self.request, pk)
        deleted_count, deleted = model.objects.filter(
            recipe=recipe, user=user).delete()

        if deleted_count > 0:
            return Response(
                {'detail': 'Рецепт успешно удален.'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'detail': 'Рецепт не найден.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(methods=['post'],
            detail=True,
            url_path='shopping_cart',
            permission_classes=[permissions.IsAuthenticated],
            )
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта в список покупок."""

        return self.handle_add(ShoppingCartSerializer, ShoppingCart,
                               request.user, pk)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """Удаление рецепта из списка покупок."""

        return self.handle_remove(ShoppingCartSerializer, ShoppingCart,
                        request.user, pk)

    @action(methods=['get'],
            detail=False,
            url_path='download_shopping_cart',)
    def download_shopping_cart(self, request, pk=None):
        """
        Скачивание списка покупок.
        Фильтр по RecipeIngredient, где:
        recipe__shoppingcart__user = user - это список покупок пользователя
        values('ingredient__name', 'ingredient__measurement_unit') - выбираем
        название ингредиента и единицу измерения
        annotate(amount=Sum('amount')) - суммируем количество ингредиента
        order_by('ingredient__name') - сортируем по названию
        """
        user = request.user
        shopping_cart = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcart__user=user).values(
                    'ingredient__name',
                    'ingredient__measurement_unit').annotate(
                        amount=Sum('amount')).order_by('ingredient__name'))

        downloading_file = create_list_txt(
            shopping_cart, 'Список покупок от: ')
        downloading_file = BytesIO(downloading_file.getvalue().encode('utf-8'))
        return FileResponse(
            downloading_file,
            as_attachment=True,
            filename="shopping_list.txt",
            status=status.HTTP_200_OK)

    @action(methods=['post'],
            detail=True,
            url_path='favorite',
            permission_classes=[permissions.IsAuthenticated],)
    def favorite(self, request, pk=None):
        """Добавление и удаление рецепта в избранное."""

        return self.handle_add(FavoriteSerializer, Favorite,
                               request.user, pk)

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        """Удаление рецепта из избранного."""

        return self.handle_remove(FavoriteSerializer, Favorite,
                                  request.user, pk)
