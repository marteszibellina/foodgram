# -*- coding: utf-8 -*-

# [ОГРАНИЧЕНИЕ ЗНАЧЕНИЙ]
# Ингридиенты
MAX_INGRED_NAME_LENGTH = 128
MAX_INGRED_MEASURE_LENGTH = 64
MIN_INGREDIENT_AMOUNT = 1
MAX_INGREDIENT_AMOUNT = 10000

# Теги
MAX_TAG_NAME_LENGTH = 32
MAX_TAG_SLUG_LENGTH = 32

# Рецепты
MAX_RECIPE_NAME = 256
# MAX_RECIPE_TEXT = 2000
MIN_RECIPE_NAME = 2
# MAX_RECIPE_TEXT_LENGTH = 1024
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32767  # 32767 минут ~= 22 дня

# Для всех моделей
TEXT_SLICE = 20


# [СООБЩЕНИЯ]
# Время готовки
COOKING_TIME_ERROR = 'Время приготовления должно быть от 1 до 600 минут.'
INGREDIENT_AMOUNT_ERROR = 'Количество ингридиентов должно быть больше 1.'
