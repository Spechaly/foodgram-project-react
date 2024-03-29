from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import UniqueConstraint

User = get_user_model()


class Ingredient(models.Model):
    """Модель Ингредиентов"""
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=256,)
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=256
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name} измеряется в {self.measurement_unit}'


class Recipe(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        User,
        verbose_name='Автор рецепта',
        related_name='recipes',
        on_delete=models.SET_NULL,
        null=True
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=256
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингридиенты в рецепте',
        related_name='recipes',
        through='IngredientInRecipe'
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления, мин',
        validators=[MinValueValidator(
            1, message='Минимальное время приготовления 1 минута')
        ]
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Модель тегов"""
    name = models.CharField(
        verbose_name='Наименование тега',
        max_length=256,
        unique=True
    )
    color = models.CharField(
        verbose_name='HEX цвет',
        unique=True,
        max_length=7,
        validators=[
            RegexValidator(
                regex='^#[A-Fa-f0-9]{6}$',
                message='Введите значение цвета в HEX! Пример:#49B64E'
            )
        ]
    )
    slug = models.SlugField(
        verbose_name='Слаг тега',
        max_length=256,
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Промежуточная модель для связи рецепта и ингредиента"""
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт',
        related_name='ingredients_in_recipe',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Ингредиент',
        related_name='ingredients_in_recipe',
        on_delete=models.CASCADE
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1, message='Минимальное количество 1!')]
    )

    class Meta:
        verbose_name = 'Количество ингредиента'
        verbose_name_plural = 'Количество ингредиентов'
        constraints = [
            UniqueConstraint(fields=['recipe', 'ingredient'],
                             name='unique_ingredient')
        ]

    def __str__(self):
        return (
            f'колличество {self.ingredient.name} в'
            f'{self.ingredient.measurement_unit} равно {self.amount}'
        )


class Favourite(models.Model):
    """Модель избранного"""
    user = models.ForeignKey(
        User,
        verbose_name='Юзер с избранным',
        related_name='favorites',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт в избранном',
        related_name='favorites',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Избраный'
        verbose_name_plural = 'Избранные'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_favorite')
        ]

    def __str__(self):
        return (
            f'{self.user} добавил в избранное {self.recipe}'
        )


class ShoppingList(models.Model):
    '''Модель корзины покупок'''
    user = models.ForeignKey(
        User,
        verbose_name='Юзер',
        related_name='shopping',
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        verbose_name='Рецепт в корзине',
        related_name='shopping',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Список покупок'
        constraints = [
            UniqueConstraint(fields=['user', 'recipe'],
                             name='unique_shopping_list')
        ]

    def __str__(self):
        return (
            f'{self.user} добавил в корзину {self.recipe}'
        )
