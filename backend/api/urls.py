# -*- coding: utf-8 -*-

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.routers import DefaultRouter, SimpleRouter

# Импорт viewsets тут
from api.views import (#FavoriteViewSet,
                       IngredientViewSet,
                       RecipeViewSet,
                       #ShoppingCartViewSet,
                       #SubscribeViewSet,
                       TagViewSet,
                       UserViewSet)

router = DefaultRouter()  # Роутер API

# Регистрация путей роутера тут
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
# router.register('favorite', FavoriteViewSet, basename='favorite')
# router.register('shopping_list', ShoppingCartViewSet,
                #    basename='shopping_list')
router.register('users', UserViewSet, basename='users')
# router.register('subscribtions', SubscribeViewSet, basename='subscribe')

router_v1_simple = SimpleRouter()  # Роутер v1 для гибкой настройки

# Регистрация гибкого пути роутера тут


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
# urlpatterns += [
#     path('api/recipes/download_shopping_cart/',
#          RecipeViewSet.as_view({'get': 'download_shopping_cart'},
#                                name='download_shopping_cart'))
# ]
