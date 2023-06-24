# Проект Foodgram


## Описание

Проект Foodgram - это продуктовый помошник, в котором вы можете создавать рецепты, добавлять их в избранные, подписываться на людей и следить за их новинками кулинарии. Так же доступен для скачивания чеклист,чтобы сходить в магазин и купить все необходимое в рецепте!  


## Установка для локального пользования

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


## Установка для разворачивания проекта на сервере

- Клонировать репозиторий с github:
```git clone ... ```
- Установить на сервере Docker, Docker Compose.
- Скопировать на сервер файлы docker-compose.yml, nginx.conf из папки infra:
```scp docker-compose.yml nginx.conf username@IP:/home/username/   # username - имя пользователя на сервере```
                                                                ```# IP - публичный IP сервера```
- Для работы с GitHub Actions необходимо в репозитории в разделе Secrets > Actions создать переменные окружения:
```
SECRET_KEY              # секретный ключ Django проекта
DOCKER_PASSWORD         # пароль от Docker Hub
DOCKER_USERNAME         # логин Docker Hub
HOST                    # публичный IP сервера
USER                    # имя пользователя на сервере
PASSPHRASE              # *если ssh-ключ защищен паролем
SSH_KEY                 # приватный ssh-ключ

DB_ENGINE               # django.db.backends.postgresql
DB_NAME                 # postgres
POSTGRES_USER           # postgres
POSTGRES_PASSWORD       # postgres
DB_HOST                 # db
DB_PORT                 # 5432 (порт по умолчанию)```
```
- Cоздать и запустить контейнеры Docker:
```sudo docker-compose up -d```
- Выполнить миграции:
```sudo docker-compose exec backend python manage.py migrate```
- Создать суперпользователя:
```sudo docker-compose exec backend python manage.py createsuperuser```
- Создать статику:
```sudo docker-compose exec backend python manage.py collectstatic --noinput:```
- Выполнить команду для загрузки ингридиентов::
```sudo docker-compose exec backend python manage.py loadingridientsdata```

- Можно пользоваться проектом по ссылке:
```http://158.160.70.34/```


## Автор проекта:
- Евгений Балуев
