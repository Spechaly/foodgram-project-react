from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    """Кастомная модель пользователя основанная на User"""
    # email делаю уникальным, чтобы можно было различать пользователей
    # при аутентификации
    email = models.EmailField(
        verbose_name='Почта',
        max_length=256,
        unique=True
    )
    # Для аутентификации используем код ниже, чтобы входить по email и password
    # authenticate(email password) вместо authenticate(username password)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name'
    ]

    class Meta:
        # Добавлю наименования моделей в единственном и множественном числах
        # для админки
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    # Добавлю функцию вывода, при обращении к классу
    def __str__(self):
        return self.username


class Subscribe (models.Model):
    """Модель содержащая в себе подписки на авторов"""
    # Связываю юзера подписок с моделью юзера методом многие-к-одному
    # c каскадным удалением связи, при удалении юзера
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        related_name='subscriber',
        on_delete=models.CASCADE,
    )
    # Связываю автора рецепта модели подписок с моделью юзера методом
    # многие-к-одному c каскадным удалением связи, при удалении юзера(автора)
    author = models.ForeignKey(
        User,
        verbose_name='Автор',
        related_name='subscribing',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        # Важно чтобы было наложено ограничение на повторную подписку
        # сделаю это через уникальный набор сочетаний столбцов юзера и автора
        constraints = [
            UniqueConstraint(fields=['user', 'author'],
                             name='unique_subscription')
        ]

    # Добавлю функцию вывода, при обращении к классу
    def __str__(self):
        return f'{self.user} подписался на {self.author}'
