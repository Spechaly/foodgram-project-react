from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscribtions, User


# Регистрирую модель юзера в админ панели
# делаю возможность фильтра по емайл и имени
@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = (
        'username',
        'id',
        'email',
        'first_name',
        'last_name',
    )
    list_filter = ('email', 'first_name')


# Регистрирую модель подписок в админ панели
@admin.register(Subscribtions)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user', 'author',)
