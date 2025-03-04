# -*- coding: utf-8 -*-
"""
Загрузка csv-файла

@author: marteszibelina
"""

import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """
    Команда загрузки csv-файла ингредиентов.
    Управление на python: manage.py csv_import
    """

    help = "Загрузка csv-файла ингредиентов"

    def handle(self, *args, **options):
        """Метод загрузки csv-файла ингредиентов"""
        number = Ingredient.objects.count()
        reader = csv.DictReader(
            open('./data/ingredients.csv', encoding='utf-8'),
            fieldnames=[
                'name',
                'measurement_unit',
            ],
        )
        Ingredient.objects.bulk_create(
            [Ingredient(**data) for data in reader],
        )
        if Ingredient.objects.count() > number:
            self.stdout.write('Ингредиенты успешно загружены')
        else:
            self.stdout.write('Ошибка загрузки')
