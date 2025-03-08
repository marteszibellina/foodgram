# -*- coding: utf-8 -*-

from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Разрешение только для автора."""

    def has_object_permission(self, request, view, obj):
        """Проверка на автора или администратора."""
        return (request.user == obj.author
                or request.method in permissions.SAFE_METHODS)  # О_О так можно
