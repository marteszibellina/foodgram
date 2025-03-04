# -*- coding: utf-8 -*-
"""
URLs для приложения api, работающая с Recipes и Users

@author: marteszibellina
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter

# Импорт viewsets тут
from api.views import (FavoriteViewSet, IngredientViewSet, RecipeViewSet,
                       ShoppingCartViewSet, SubscribeViewSet, TagViewSet,
                       UserViewSet)

router_v1 = DefaultRouter()  # Роутер API v1

# Регистрация путей роутера тут
router_v1.register(r'recipes', RecipeViewSet, basename='recipes')
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='ingredients')
router_v1.register('favorite', FavoriteViewSet, basename='favorite')
router_v1.register('shopping_list', ShoppingCartViewSet, basename='shopping_list')
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('subscribtions', SubscribeViewSet, basename='subscribe')

router_v1_simple = SimpleRouter()  # Роутер v1 для гибкой настройки

# Регистрация гибкого пути роутера тут


urlpatterns = [
    path('', include(router_v1.urls)),
    # path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
urlpatterns += [
    path('api/recipes/download_shopping_cart/',
         RecipeViewSet.as_view({'get': 'download_shopping_cart'},
                               name='download_shopping_cart'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
