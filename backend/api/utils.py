# -*- coding: utf-8 -*-

import datetime as dt
import io

from django.conf import settings
from django.core.mail import send_mail
from recipes.models import RecipeIngredient
from rest_framework import serializers

from users.models import Subscriptions


# def send_confirmation_email(user, confirmation_code):
#     """Отправка подтверждения регистрации"""
#     subject = 'Подтверждение регистрации FoodGram'
#     message = (f'Ваш код подтверждения {confirmation_code}.',
#                'Если Вы не делали запрос на регистрацию,',
#                'то проигнорируйте это письмо.')
#     from_email = settings.DEFAULT_FROM_EMAIL
#     recipient_list = [user.email]
#     send_mail(subject, message, from_email, recipient_list)

# Перенести в статикметод сериализатора

def check_favorite_in_list(request, obj, model):
    """Проверка на наличие в избранном."""
    if not request:
        return False
    return (request.user.is_authenticated and model.objects.filter(
        user=request.user, recipe__id=obj.id).exists())


def create_list_txt(shopping_list, text):
    """Создание списка покупок в формате txt."""
    # Получаем текущую дату
    date_today = dt.datetime.now()
    # Создаем текстовый поток
    file = io.StringIO()

    # Создадим заголовок
    file.write(f'{text} {date_today.strftime("%d.%m.%Y")}:\n\n')

    # Перебираем список покупок
    for num, obj in enumerate(shopping_list, 1):
        file.write(f'{num}. {obj["ingredient__name"]} - '
                   f'{obj["amount"]}'
                   f' {obj["ingredient__measurement_unit"]},\n')
    # Закрываем поток
    file.seek(0)
    return file


# Класс сериализатора подписки
# Используется как утилита, расширяя функциональность сериализаторов
class UserSubscribe(metaclass=serializers.SerializerMetaclass):
    """Сериализатор подписки."""

    # Проверка на наличие подписки
    # Используем SerializerMethodField для получения значения
    # в методе get_is_subscribed
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        """Проверка на наличие подписки."""
        request = self.context.get('request')
        return not (request is None or request.user.is_anonymous) and \
            Subscriptions.objects.filter(
                user=request.user, author=obj.id).exists()  # O_O

        # if request is None or request.user.is_anonymous:
        #     return False
        # # Проверяем, есть ли подписка
        # return Subscriptions.objects.filter(
        #     user=request.user, author=obj.id).exists()


def create_short_link(recipe_id: int, request) -> str:
    """Создает прямую ссылку на рецепт."""
    base_url = request.build_absolute_uri('/')[:-1]
    return f"{base_url}/recipes/{recipe_id}"
