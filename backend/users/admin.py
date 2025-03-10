# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from users.models import Subscriptions

User = get_user_model()


@admin.register(User)
class FoodGramUserAdmin(UserAdmin):
    """Модель администрирования пользователя"""

    list_display = ('pk',
                    'username',
                    'email',
                    'first_name',
                    'last_name',
                    'date_joined')
    list_display_links = ('pk', 'username', 'email',)
    search_fields = ('username', 'email',)
    list_filter = ('username', 'email',)
    empty_value_display = '-пусто-'


@admin.register(Subscriptions)
class SubsriptionsAdmin(admin.ModelAdmin):
    """Модель администрирования подписок"""

    list_display = ('pk', 'user', 'author',)
    list_display_links = ('user', 'author',)
    search_fields = ('user', 'author',)
    list_filter = ('user',)


admin.site.unregister(Group)
admin.site.site_header = 'FoodGram. Администрирование.'
