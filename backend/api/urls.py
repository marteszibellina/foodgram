# -*- coding: utf-8 -*-

from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter

# Импорт viewsets тут
from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router = DefaultRouter()  # Роутер API

# Регистрация путей роутера тут
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register(r'users', UserViewSet, basename='users')

router_v1_simple = SimpleRouter()  # Роутер v1 для гибкой настройки

# Регистрация гибкого пути роутера тут


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
