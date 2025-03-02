# -*- coding: utf-8 -*-
"""
Константы для модели рецептов.

@author: marteszibellina
"""

# [ОГРАНИЧЕНИЕ ЗНАЧЕНИЙ]
# Ингридиенты
MAX_INGRED_NAME_LENGTH = 128
MAX_INGRED_MEASURE_LENGTH = 64
MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 200

# Теги
MAX_TAG_NAME_LENGTH = 32
MAX_TAG_SLUG_LENGTH = 32
MAX_TAG_HEX_COLOR_LENGTH = 7  # Максимальная длина HEX-цвета #FFFFFF=(7)

# Рецепты
MAX_RECIPE_NAME = 256
MAX_RECIPE_TEXT = 2000
MIN_RECIPE_NAME = 2
MAX_RECIPE_TEXT_LENGTH = 1024
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 600

# Для всех моделей
TEXT_SLICE = 20


# [СООБЩЕНИЯ]
# Время готовки
COOKING_TIME_ERROR = f'Время приготовления должно быть от {MIN_COOKING_TIME} до {MAX_COOKING_TIME} мин.'
INGREDIENT_AMOUNT_ERROR = 'Количество ингридиентов должно быть больше 1.'
