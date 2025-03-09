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
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeCreateSerializer, SubscribeRecipeSerializer,
                             ShoppingCartSerializer, SubscribeCreateSerializer,
                             SubscribeViewSerializer, TagSerializer,
                             RecipeViewSubscriptionSerializer,
                             UserAvatarSerializer, UserViewSerializer,
                             )
from api.utils import create_list_txt, create_short_link
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscriptions

User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""

    # http_method_names = ['get', ]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов."""

    # http_method_names = ['get', ]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filterset_class = IngredientFilter

    # def get_permissions(self):
    #     if self.action == 'list':
    #         return [permissions.AllowAny()]
    #     elif self.action in ('create', 'update', 'partial_update', 'destroy'):
    #         raise exceptions.MethodNotAllowed(self.request.method)
    #     return super().get_permissions()


class UserViewSet(UVS):
    """Вьюсет для пользователей."""

    queryset = User.objects.all()
    # serializer_class = UserCreateSerializer
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
        # if request.method == 'PUT':
        user = get_object_or_404(User, id=request.user.id)
        serializer = UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара."""
        # user = get_object_or_404(User, id=request.user.id)
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
        # if request.method == 'POST':
        recipes_limit = int(request.query_params.get('recipes_limit', 3))
        author = get_object_or_404(User, id=id)
        user = self.request.user
        recipe = self.request.data.get('recipe')
        # Передаем объект 'author' через context
        serializer = SubscribeCreateSerializer(
            context={'request': request},
            data={'author': author.id, 'user': user.id})
            # context={'request': request,
            #             'recipes_limit': recipes_limit,
            #             'author': author})
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

    def get_queryset(self):
        """Получение списка рецептов."""
        queryset = Recipe.objects.all()
        if self.request.user.is_anonymous:
            return queryset
            # queryset = queryset.annotate(
            #     is_favorited=Exists(Favorite.objects.filter(
            #         user=self.request.user, recipe_id=OuterRef('pk')
            #     )),
            #     is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
            #         user=self.request.user, recipe_id=OuterRef('pk')
            #     ))
            # )
        return queryset.with_favorites_and_shopping_cart(self.request.user)

    def get_permissions(self):
        """Получение прав."""
        if self.action in ('get', 'list', 'retrieve', 'get_link'):
            return (permissions.IsAuthenticatedOrReadOnly(),
                    IsAuthorOrReadOnly())
        elif self.action in ('create', 'post', 'patch', 'update',
                             'partial_update', 'destroy'):
            return (IsAuthorOrReadOnly(),
                    permissions.IsAuthenticatedOrReadOnly())
        return super().get_permissions()

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

    def handle_add(self, serializer_class, model, data):
        """Добавление рецепта: избранное, список покупок."""
        serializer = serializer_class(
            data=data,
            context={'request': self.request})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(user=self.request.user)
        return instance

    def handle_remove(self, serializer_class, model, data):
        """Удаление рецепта: избранное, список покупок."""
        deleted_count, deleted = model.objects.filter(
            recipe=data['recipe'], user=data['user']).delete()
        return deleted_count

    @action(methods=['post'],
            detail=True,
            url_path='shopping_cart',
            permission_classes=[permissions.IsAuthenticated],
            )
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта в список покупок."""
        recipe = self.get_recipe(request, pk)
        # if request.method == 'POST':
        if ShoppingCart.objects.filter(
                user=request.user, recipe=recipe).exists():
            return Response(
                {'detail': 'Рецепт уже в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = {'recipe': recipe.id, 'user': request.user.id}
        instance = self.handle_add(
            ShoppingCartSerializer, ShoppingCart, data)
        recipe_serializer = RecipeViewSubscriptionSerializer(instance.recipe)
        # recipe_serializer = RecipeViewSerializer(instance.recipe)
        return Response(recipe_serializer.data,
                        status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        """Удаление рецепта из списка покупок."""
        recipe = self.get_recipe(request, pk)
        user = request.user
        data = {'recipe': recipe.id, 'user': user.id}
        deleted = self.handle_remove(
            ShoppingCartSerializer, ShoppingCart, data)
        if deleted > 0:
            return Response(
                {'detail': 'Рецепт удален из списка покупок.'},
                status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепт не найден в списке покупок.'},
            status=status.HTTP_400_BAD_REQUEST)
        # shopping_cart = ShoppingCart.objects.filter(
        #     user=user, recipe=recipe).first()
        # if shopping_cart:
        #     shopping_cart.delete()
        #     return Response(
        #         {'detail': 'Рецепт удален из списка покупок.'},
        #         status=status.HTTP_204_NO_CONTENT)
        # return Response(
        #     {'detail': 'Рецепт не найден в списке покупок.'},
        #     status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['get'],
            detail=False,
            url_path='download_shopping_cart',)
    def download_shopping_cart(self, request, pk=None):
        """Скачивание списка покупок."""
        user = request.user
        # Список покупок:
        # Фильтр по RecipeIngredient, где:
        # recipe__shoppingcart__user = user - это список покупок пользователя
        # values('ingredient__name', 'ingredient__measurement_unit') - выбираем
        # название ингредиента и единицу измерения
        # annotate(amount=Sum('amount')) - суммируем количество ингредиента
        # order_by('ingredient__name') - сортируем по названию
        shopping_cart = (
            # Отфильтровать RecipeIngredient
            RecipeIngredient.objects.filter(
                # где recipe__shoppingcart__user - это список покупок
                recipe__shoppingcart__user=user)
            # выбираем: ингредиент и единицу измерения
            .values('ingredient__name', 'ingredient__measurement_unit')
            # суммируем количество
            .annotate(amount=Sum('amount'))
            # сортируем по названию ингредиента
            .order_by('ingredient__name'))

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
    def favorite(self, request, pk):
        """Добавление и удаление рецепта в избранное."""
        recipe = self.get_recipe(request, pk)
        # if request.method == 'POST':
        data = {'user': request.user.id,'recipe': recipe.id}
            # if Favorite.objects.filter(
            #         user=request.user, recipe=recipe).exists():
            #     return Response(
            #         {'detail': 'Рецепт уже в избранном.'},
            #         status=status.HTTP_400_BAD_REQUEST
            #     )
        self.handle_add(FavoriteSerializer, Favorite, data)
        # recipe_data = {
        #     'id': recipe.id,
        #     'name': recipe.name,
        #     'image': recipe.image.url if recipe.image else None,
        #     'cooking_time': recipe.cooking_time
        # }
        recipe_data = SubscribeRecipeSerializer(recipe).data
        return Response(recipe_data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def remove_from_favorite(self, request, pk=None):
        """Удаление рецепта из избранного."""
        recipe = self.get_recipe(request, pk)
        user = request.user
        data = {'recipe': recipe.id, 'user': user.id}
        removed = self.handle_remove(FavoriteSerializer, Favorite, data)
        if removed > 0:
            return Response(
                {'detail': 'Рецепт удален из избранного.'},
                status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'detail': 'Рецепт не найден в избранном.'},
            status=status.HTTP_400_BAD_REQUEST
        )
        # favorite = Favorite.objects.filter(
        #     user=user, recipe=recipe).first()
        # if favorite:
        #     return Response({
        #         'detail': 'Рецепт удален из избранного.'
        #     }, status=status.HTTP_204_NO_CONTENT)
        # return Response(
        #     {'detail': 'Рецепт не найден в избранном.'},
        #     status=status.HTTP_400_BAD_REQUEST)
