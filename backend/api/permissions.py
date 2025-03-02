# -*- coding: utf-8 -*-
"""
Разрешения для приложения api, работающая с Recipes и Users

@author: marteszibellina
"""

from rest_framework import permissions


class AdminOrCurrentUser(permissions.BasePermission):
    """Разрешение для администратора или текущего пользователя."""

    def has_permission(self, request, view):
        """Проверка на авторизацию"""
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Проверка на администратора или текущего пользователя."""
        return request.user.is_superuser or request.user == obj.author


class ReadOnly(permissions.BasePermission):
    """Разрешение только для чтения."""

    def has_permission(self, request, view):
        """Проверка на разрешение только для чтения."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return False


class AuthorOrReadOnly(permissions.BasePermission):
    """Разрешение только для автора."""

    def has_permission(self, request, view):
        """Проверка на авторизацию."""
        return (request.user.is_authenticated or request.method in permissions.
                SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        """Проверка на автора или администратора."""
        return (request.user == obj.author or request.method in permissions.
                SAFE_METHODS)
