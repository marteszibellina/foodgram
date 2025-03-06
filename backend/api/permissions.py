# -*- coding: utf-8 -*-

from rest_framework import permissions


class IsAdminOrCurrentUser(permissions.BasePermission):
    """Разрешение для администратора или текущего пользователя."""

    def has_permission(self, request, view):
        """Проверка на авторизацию"""
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Проверка на администратора или текущего пользователя."""
        return request.user.is_superuser or request.user == obj.author


class IsReadOnly(permissions.BasePermission):
    """Разрешение только для чтения."""

    def has_permission(self, request, view):
        """Проверка на разрешение только для чтения."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return False


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешение только для автора."""

    def has_object_permission(self, request, view, obj):
        """Проверка на автора или администратора."""
        return (request.user == obj.author
                or request.method in permissions.SAFE_METHODS)  # О_О так можно
