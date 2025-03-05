# «Дипломный проект FoodGram»

## Описание:

Foodgram - приложение для публикации, просмотра и поиска рецептов.
Создавайте свои рецепты, делитесь ими, добавляйте в избранное понравившиеся рецепты и собирайте список покупок, который
можно скачать в формате TXT.

## Технологии:

- python 3.9
- Django
- Django REST Framework
- Djoser
- PostgreSQL
- Nginx
- Gunicorn
- Docker

## Установка и запуск проекта:

1. Установите Docker и Docker-compose
```
sudo apt install docker.io
sudo apt-get update
sudo apt-get install docker-compose-plugin
``` 

2. Создайте файл .env в папке со скопированными из репозитория файлами со следующим содержимым:
```
# [settings]
DJANGO_ALLOWED_HOSTS= ваш хост или localhost (123.456.789.777 localhost)
DEBUG=False или True (для отладки)

# [postgresql]
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password

# [data base settings]
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
```

3. Склонируйте репозиторий
```
git clone git@github.com:marteszibellina/foodgram.git
```

4. В корневой папке foodgram запустите проект:
```
sudo docker-compose up -d --build
```

5. Создайте суперпользователя для сайта:
```
sudo docker-compose exec -t <CONTAINER ID> python3 manage.py createsuperuser
```
Обязательные поля:
- Никнейм
- Почта
- Имя
- Фамилия
- Пароль

6. Загрузите ингредиенты в проект:
```
sudo docker-compose exec -t <CONTAINER ID> python3 manage.py csv_import
```
Ингредиенты находятся по пути: backend/data/ingredients.csv

7. Зайдите в админ-зону сайта и создайте теги рецептов (вход по никнейму и паролю).
По умолчанию тегов нет, но создавать их может только администратор.
Потребуется придумать название тега и его slug.

Пример:
```
Название: Breakfast
slug: breakfast
```

### Примеры запросов:

Для взаимодействия с ресурсами настроены следующие эндпоинты:
- `api/users/` (GET, POST): передаём логин, имя, фамилию, почту и пароль - создается новый пользователь.
- `api/users/me/` (GET, POST): данные или изменить о себе.
- `api/users/{user_id}/` (GET): получить данные о другом пользователе (для подписки, просмотра рецептов автора).
- `api/auth/token/login/` (POST): передаём email и пароль, получаем токен (авторизация).
- `api/auth/token/login/` (POST): передаём токен в заголовке, далее - выход из лк.
- `api/recipes/` (GET, POST): получаем список всех рецептов или создаём новый рецепт.
- `api/recipes/{recipes_id}/` (GET, PUT, PATCH, DELETE): получаем, редактируем или удаляем рецепт по id.
- `api/tags/` (GET): получаем список всех тегов.
- `api/tags/{tag_id}/` (GET):  получаем информацию о теге по id.
- `api/igredients/` (GET): получаем список всех ингредиентов.
- `api/igredients/{igredient_id}/` (GET):  получаем информацию о ингредиенте по id.
- `api/recipes/{recipes_id}/favorite` (GET, POST): подписаться, отписаться или получить список всех избранных постов.
- `api/recipes/{recipes_id}/cart` (GET, POST): добавить, удалить или получить список всех рецептов в корзине.
- `api/recipes/download_shopping_cart` (GET): получить список ингредиентов в формате .txt.

## Дипломный проект подготовил:

<h3 align="center"><a href="https://github.com/marteszibellina" target="_blank">Дмитрий Соболев</a> 
</h3>
