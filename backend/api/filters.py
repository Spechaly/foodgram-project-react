from django_filters import rest_framework as filters

from recipes.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Фильтр рецептов."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    author = filters.NumberFilter(field_name='author__id')

    class Meta:
        model = Recipe
        fields = ('tags', 'author')