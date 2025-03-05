# -*- coding: utf-8 -*-

from io import BytesIO

from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum
from django.http import FileResponse
from django.shortcuts import get_list_or_404, get_object_or_404
from djoser.views import UserViewSet as UVS
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsReadOnly  #,  IsAdminOrCurrentUser, 
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeShortSerializer,
                             #  RecipeViewSerializer,
                             ShoppingCartSerializer,
                             SubscribeCreateSerializer, TagSerializer,
                             UserAvatarSerializer,  # UserCreateSerializer,
                             UserViewSerializer, SubscribeViewSerializer)
from api.utils import create_list_txt, create_short_link
from users.models import Subscriptions

User = get_user_model()


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для тегов."""

    http_method_names = ['get', ]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для ингредиентов."""

    http_method_names = ['get', ]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsReadOnly,)
    pagination_class = None
    filterset_class = IngredientFilter


class UserViewSet(UVS):
    """Вьюсет для пользователей."""

    queryset = User.objects.all()
    # serializer_class = UserCreateSerializer
    permission_class = (permissions.AllowAny, IsReadOnly)
    pagination_class = CustomPagination

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

    @action(detail=True,
            methods=['put',],
            url_path='avatar',)
            # permission_class=[IsAdminOrCurrentUser])
    def set_avatar(self, request, id):
        """Смена или добавление аватара."""
        user = get_object_or_404(User, id=id)
        serializer = UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @set_avatar.mapping.delete
    def delete_avatar(self, request, id):
        """Удаление аватара."""
        user = get_object_or_404(User, id=id)
        if user.avatar:
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @set_avatar.mapping.get
    def get_avatar(self, request, id):
        """Получение аватара."""
        user = get_object_or_404(User, id=id)
        if not user.avatar:
            return Response({'detail': 'Аватар не найден'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({'avatar': user.avatar.url},
                        status=status.HTTP_200_OK)

    @action(detail=True,
            methods=['post',],
            url_path='subscribe',
            permission_classes=[permissions.IsAuthenticated],
            pagination_class=CustomPagination)
    def subscribe(self, request, id):
        """Подписка на пользователя."""
        if request.method == 'POST':
            recipes_limit = int(request.query_params.get('recipes_limit', 3))
            author = get_object_or_404(User, id=id)
            user = self.request.user
            recipe = self.request.data.get('recipe')
            # Передаем объект 'author' через context
            serializer = SubscribeCreateSerializer(
                data={'user': user.id, 'recipe': recipe},
                context={'request': request,
                         'recipes_limit': recipes_limit,
                         'author': author}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id):
        """Отписка от пользователя."""
        author = self.get_object()
        user = request.user
        Subscriptions.objects.filter(user=user, author=author).delete()
        return Response(
            {'detail': 'Вы отписались от этого автора'},
            status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['get'],
            url_path='subscriptions',
            permission_classes=[permissions.IsAuthenticated],
            pagination_class=CustomPagination)
    def subscriptions(self, request):
        """Получение списка подписок."""
        serializer = SubscribeViewSerializer()
        queryset = (
            Subscriptions.objects.filter(user=request.user)
            .select_related('author')
            .prefetch_related('author__recipes')
            .order_by('-author__id')
        )

        pages = self.paginate_queryset(queryset)

        serializer = SubscribeViewSerializer(
            pages,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""

    serializer_class = RecipeCreateSerializer
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        """Получение списка рецептов."""
        queryset = Recipe.objects.all()
        if not self.request.user.is_anonymous:
            queryset = queryset.annotate(
                is_favorited=Exists(Favorite.objects.filter(
                    user=self.request.user, recipe_id=OuterRef('pk')
                )),
                is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                    user=self.request.user, recipe_id=OuterRef('pk')
                ))
            )
        return queryset

    def get_serializer_class(self):
        """Получение сериализатора."""
        if self.request.method in permissions.SAFE_METHODS:
            return self.serializer_class
        return RecipeCreateSerializer

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
        deleted_count, _ = model.objects.filter(
            data=data, request=self.request).delete()
        return deleted_count

    @action(methods=['post', 'delete'],
            detail=True,
            url_path='shopping_cart',
            permission_classes=[permissions.IsAuthenticated],
            )
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта в список покупок."""
        recipe = self.get_recipe(request, pk)
        if request.method == 'POST':
            data = {'recipe': recipe.id}
            instance = self.handle_add(
                ShoppingCartSerializer, ShoppingCart, data)
            recipe_serializer = RecipeShortSerializer(instance.recipe)
            return Response(recipe_serializer.data,
                            status=status.HTTP_201_CREATED)

        deleted = self.handle_remove(ShoppingCart, recipe.id, request.user)
        if deleted == 0:
            return Response(
                {'detail': 'Рецепт не найден в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'],
            detail=False,
            url_path='download_shopping_cart',)
    def download_shopping_cart(self, request, pk=None):
        """Скачивание списка покупок."""
        shopping_cart = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user).values(
                'ingredient__name',
                'ingredient__measurement_unit').annotate(
                    amount=Sum('amount')).order_by('ingredient__name')
        downloading_file = create_list_txt(
            shopping_cart, 'Список покупок от: ')
        downloading_file = BytesIO(downloading_file.getvalue().encode('utf-8'))
        return FileResponse(
            downloading_file,
            as_attachment=True,
            filename="shopping_list.txt",
            status=status.HTTP_200_OK)

    @action(methods=['post', 'delete'],
            detail=True,
            url_path='favorite',
            permission_classes=[permissions.IsAuthenticated],)
    def favorite(self, request, pk):
        """Добавление и удаление рецепта в избранное."""
        recipe = self.get_recipe(request, pk)
        if request.method == 'POST':
            data = {
                'user': request.user.id,
                'recipe': recipe.id
            }
            serializer = self.handle_add(
                FavoriteSerializer, Favorite, data)
            recipe_data = {
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image.url if recipe.image else None,
                'cooking_time': recipe.cooking_time
            }
            return Response(recipe_data, status=status.HTTP_201_CREATED)
    
        favorite = self.handle_remove(Favorite, recipe.id, request.user).first()
        if favorite:
            return Response({
                'detail': 'Рецепт удален из избранного.'
            }, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({
                'detail': 'Рецепт не найден в избранном.'
            }, status=status.HTTP_400_BAD_REQUEST)
