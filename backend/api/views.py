# -*- coding: utf-8 -*-
"""
Вьюсеты для приложения api, работаюшее с Recipes и Users.

@author: marteszibellina
"""
from io import BytesIO
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Sum, Count
from django.http import FileResponse
from django.shortcuts import get_object_or_404, get_list_or_404

from djoser.views import UserViewSet as UVS

from rest_framework import status, serializers, viewsets, exceptions
from rest_framework.decorators import action, api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework import permissions
from rest_framework.response import Response

from api.filters import RecipeFilter, IngredientFilter
from api.serializers import (TagSerializer,
                             IngredientSerializer,
                             RecipeViewSerializer,
                             RecipeCreateSerializer,
                             ShoppingCartSerializer,
                             UserViewSerializer,
                             UserCreateSerializer,
                             UserPasswordSerializer,
                             UserAvatarSerializer,
                             SubscribeSerializer,
                             RecipeShortSerializer,
                             FavoriteSerializer,
                             )
from api.pagination import CustomPagination
from api.permissions import (ReadOnly,
                             AdminOrCurrentUser,
                             )
from api.utils import create_list_txt, create_short_link

from recipes.models import (
    Tag,
    Ingredient,
    Recipe,
    RecipeIngredient,
    Favorite,
    ShoppingCart,
)
from users.models import Subscriptions

User = get_user_model()


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для тегов."""

    http_method_names = ['get',]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    # Доступно всем
    permission_classes = (permissions.AllowAny,)
    # Пагинация не требуется
    pagination_class = None

    def get_permissions(self):
        if self.action == 'list':
            return [permissions.AllowAny()]
        elif self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [AdminOrCurrentUser()]
        return super().get_permissions()


class IngredientViewSet(viewsets.ModelViewSet):
    """Вьюсет для ингредиентов."""

    http_method_names = ['get',]
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    # Доступно всем
    permission_classes = (ReadOnly,)
    # Пагинация не требуется
    pagination_class = None
    # По умолчанию: фильтрация по названию
    filterset_class = IngredientFilter

    def get_permissions(self):
        if self.action == 'list':
            return [permissions.AllowAny()]
        elif self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [AdminOrCurrentUser()]
        return super().get_permissions()


class FavoriteViewSet(viewsets.ModelViewSet):
    """Вьюсет для избранных рецептов."""

    queryset = Favorite.objects.all()
    serializer_class = RecipeViewSerializer
    # Доступно только для авторизованного пользователя
    permission_class = (permissions.IsAuthenticated,)
    # Пагинация не требуется
    pagination_class = None

    def get_queryset(self):
        """Получение списка избранных рецептов."""
        return Favorite.objects.filter(user=self.request.user)


class UserViewSet(UVS):
    """Вьюсет для пользователей."""

    serializer_class = UserCreateSerializer
    # Доступно всем
    permission_class = (permissions.AllowAny, ReadOnly)
    # Пагинация не требуется
    pagination_class = CustomPagination

    def get_queryset(self):
        """Получение списка пользователей."""
        return User.objects.all()

    def get_permissions(self):
        if self.action in ('get', 'list', 'retrieve'):
            return [permissions.AllowAny()]
        else:
            return super().get_permissions()

    def get_serializer_class(self):
        """Получение сериализатора."""
        # Если требуется сменить пароль, то возвращаем сериализатор
        if self.action == 'set_password':
            return UserPasswordSerializer
        # Если требуется создать пользователя, то возвращаем сериализатор
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'set_avatar':
            return UserAvatarSerializer
        if self.action == 'subscribe':
            return SubscribeSerializer
        if self.action == 'subscriptions':
            return SubscribeSerializer
        return UserViewSerializer

    # Получение информации о текущем пользователе
    @action(detail=False,
            methods=['get'],
            url_path='me',
            permission_class=[permissions.IsAuthenticated])
    def me(self, request):
        """Получение информации о текущем пользователе."""
        serializer = UserViewSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Создание пользователя
    def create(self, request):
        """Создание пользователя."""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Смена или добавление аватара
    @action(detail=True,
            methods=['get', 'put', 'delete'],
            url_path='avatar',
            permission_class=[AdminOrCurrentUser])
    def set_avatar(self, request, id):
        """Смена или добавление аватара."""
        if request.method == 'GET':
            user = get_object_or_404(User, id=self.request.user.id)
            if not user.avatar:
                return Response({'detail': 'Аватар не найден'},
                                status=status.HTTP_404_NOT_FOUND)
            return Response({'avatar': user.avatar.url},
                            status=status.HTTP_200_OK)
        if request.method == 'PUT':
            user = get_object_or_404(User, id=self.request.user.id)
            serializer = UserAvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            user = get_object_or_404(User, id=self.request.user.id)
            serializer = UserAvatarSerializer(user, data=request.data)
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    # Подписка на пользователя
    @action(detail=True,
            methods=['post', 'delete'],
            url_path='subscribe',
            permission_classes=[permissions.IsAuthenticated],
            pagination_class=CustomPagination)
    def subscribe(self, request, id):
        """Подписка на пользователя."""
        author = get_object_or_404(User, id=id)
        user = request.user
        recipes_limit = int(request.query_params.get('recipes_limit', 3))
        if request.method == 'POST':
            
            if Subscriptions.objects.filter(
                user=user,
                author=author
            ).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if author == user:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription = Subscriptions.objects.create(
                user=user,
                author=author
            )
            serializer = SubscribeSerializer(
                subscription,
                context={'request': request, 'recipes_limit': recipes_limit}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        get_object_or_404(
            Subscriptions,
            user=user,
            author=author
        ).delete()
        return Response({'detail': 'Подписка удалена'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=['get'],
            url_path='subscriptions',
            permission_classes=[permissions.IsAuthenticated],
            pagination_class=CustomPagination)
    def subscriptions(self, request):
        """Получение списка подписок."""
        recipes_limit = int(request.query_params.get('recipes_limit', 3))

        queryset = (
            Subscriptions.objects.filter(user=request.user)
            .select_related('author')
            .prefetch_related('author__recipes')
            .order_by('-id')
        )

        pages = self.paginate_queryset(queryset)

        serializer = SubscribeSerializer(
            pages,
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit}
        )
        return self.get_paginated_response(serializer.data)



class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с рецептами."""

    # Используем сериализатор создания рецептов по умолчанию
    serializer_class = RecipeCreateSerializer
    # Используем фильтры для рецептов
    filterset_class = RecipeFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        """Получение списка рецептов."""
        queryset = Recipe.objects.all()
        if self.request.user.is_anonymous:
            return queryset
        queryset = Recipe.objects.annotate(
            is_favorited=Exists(Favorite.objects.filter(
                user=self.request.user, recipe_id=OuterRef('pk')
            )),
            is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                user=self.request.user, recipe_id=OuterRef('pk')
            ))
        )
        if self.request.GET.get('is_favorited'):
            return queryset.filter(is_favorited=True)
        if self.request.GET.get('is_in_shopping_cart'):
            return queryset.filter(is_in_shopping_cart=True)
        return queryset

    def get_permissions(self):
        """Получение прав."""
        if self.action in ('get', 'list', 'retrieve', 'get_link'):
            return (permissions.AllowAny(),)
        elif self.action in ('create', 'post', 'patch', 'update',
                             'partial_update', 'destroy'):
            return (AdminOrCurrentUser(),)
        return (permissions.IsAuthenticated(),)

    def get_serializer_class(self):
        """Получение сериализатора."""
        if self.request.method in permissions.SAFE_METHODS:
            return self.serializer_class
        return RecipeCreateSerializer

    @action(methods=['get'],
            detail=True,
            url_path='get-link'
            )
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

    @action(methods=['post', 'delete'],
            detail=True,
            url_path='shopping_cart',
            permission_classes=[permissions.IsAuthenticated],
            )
    def shopping_cart(self, request, pk=None):
        """Добавление и удаление рецепта в список покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = ShoppingCartSerializer(
                data={'recipe': recipe.id},
                context={'request': request})
            serializer.is_valid(raise_exception=True)
            shopping_cart = serializer.save(user=request.user)
            recipe_serializer = RecipeShortSerializer(recipe)
            return Response({
                'user': serializer.data['user'],
                'recipe': recipe_serializer.data},
                status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            shopping_cart = ShoppingCart.objects.filter(
                user=request.user,
                recipe=recipe
            )
            if not shopping_cart.exists():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            shopping_cart.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=['get'],
            detail=False,
            url_path='download_shopping_cart',
            )
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
            status=status.HTTP_200_OK,
        )

    @action(methods=['post', 'delete'],
            detail=True,
            url_path='favorite',
            permission_classes=[permissions.IsAuthenticated],
            )
    def favorite(self, request, pk):
        """Добавление и удаление рецепта в избранное."""
        recipe = get_object_or_404(Recipe, id=pk)
        # В случае POST — добавляем рецепт в избранное
        if request.method == 'POST':
            # Подготовка данных для сериализатора
            data = {
                'user': request.user.id,
                'recipe': recipe.id
            }
            # Создаем и валидируем сериализатор
            serializer = FavoriteSerializer(data=data, context={"request": request})
            # Проверка на валидность
            serializer.is_valid(raise_exception=True)
            # Сохраняем избранное
            favorite = serializer.save(user=request.user)
            # Сериализуем объект Favorite
            serializer = FavoriteSerializer(favorite, context={"request": request})
            # Возвращаем полные данные рецепта
            recipe_data = {
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image.url if recipe.image else None,
                'cooking_time': recipe.cooking_time
            }
            return Response({
                'recipe': recipe_data
            }, status=status.HTTP_201_CREATED)
        # В случае DELETE — удаляем рецепт из избранного
        if request.method == 'DELETE':
            favorite = Favorite.objects.filter(user=request.user, recipe=recipe).first()
            if favorite:
                favorite.delete()
                return Response({
                    'detail': 'Рецепт удален из избранного.'
                }, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({
                    'detail': 'Рецепт не найден в избранном.'
                }, status=status.HTTP_400_BAD_REQUEST)


class SubscribeViewSet(viewsets.ModelViewSet):
    """Вьюсет для подписок."""

    http_method_names = ['get', 'list,', 'retrieve', 'post', 'delete']
    serializer_class = SubscribeSerializer
    # Доступно только для авторизованного пользователя
    permission_class = (permissions.IsAuthenticated,)
    # Пагинация не требуется
    pagination_class = CustomPagination

    def get_queryset(self):
        """Получение списка подписок."""
        # Если пользователь не авторизован, то возвращаем пустой список
        # Если авторизован, возвращаем список пользователей,
        # на которых он подписан
        return get_list_or_404(
            User.objects.filter(following__user=self.request.user))

    def get_permissions(self):
        if self.action in ('get', 'list', 'retrieve'):
            return (permissions.AllowAny(),)
        return super().get_permissions()

class ShoppingCartViewSet(viewsets.ModelViewSet):
    """Вьюсет для списка покупок."""

    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    # Доступно только для авторизованного пользователя
    permission_class = (permissions.IsAuthenticated,)
    # Пагинация не требуется
    pagination_class = None

    def get_queryset(self):
        """Получение списка покупок."""
        return ShoppingCart.objects.filter(user=self.request.user)
