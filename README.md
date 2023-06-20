# Проект Foodgram


## Описание

Проект Foodgram - это продуктовый помошник, в котором вы можете создавать рецепты, добавлять их в избранные, подписываться на людей и следить за их новинками кулинарии. Так же доступен для скачивания чеклист,чтобы сходить в магазин и купить все необходимое в рецепте!  


## Установка

- Клонировать репозиторий с github:
```git clone ... ```
- Cоздать и активировать виртуальное окружение:
```python -m venv venv ```
```source venv/scripts/activate```
- Установить зависимости из файла requirements.txt:
```python -m pip install --upgrade pip```
```pip install -r requirements.txt```
- Запустить контейнеры из папки infra:
```docker-compose up -d --build```
- Выполнить миграции в контейнере:
```docker-compose exec backend python manage.py migrate```
- Создать суперюзера:
```docker-compose exec backend python manage.py createsuperuser```
- Собрать статику:
```docker-compose exec backend python manage.py collectstatic --no-inpu```
- Выполнить команду для загрузки ингридиентов:
```docker-compose exec backend python manage.py loadingridientsdata```
- Зайти в админ панель и задать Теги:
```например завтрак обед и ужин```
- Можно пользоваться проектом по ссылке:
```http://localhost```


## Автор проекта:
- Евгений Балуев
