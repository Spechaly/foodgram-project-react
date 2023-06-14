from django.contrib import admin
from .models import (
    Recipe, Ingredient,
    Tag, IngredientRecipe, Favourite, ShoppingList)


# Регистрирую модель рецепта в админку с полями автор и название
# рецепта. фильтрую еще по тегам!!! странно тогда почему теги не добавить
# в отображение если по ним фильтруем??
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'name'
    )
    list_filter = ('author', 'name', 'tags')
    # добавляем в админку только для просмотра
    readonly_fields = ('count_favorites')

    def count_favorites(self, obj):
        return obj.favorites.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    list_filter = ('name')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color',
        'slug'
    )


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recip'
    )


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = (
        'recip',
        'ingredient',
        'amount'
    )


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'recip'
    )
