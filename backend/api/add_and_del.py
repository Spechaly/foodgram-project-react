from django.shortcuts import get_object_or_404
from recipes.models import Recipe
from rest_framework import status
from rest_framework.response import Response


def add_and_del(self, request, serializer, model_1, **kwargs):
    recipe = get_object_or_404(Recipe, id=kwargs['pk'])
    data = request.data.copy()
    data.update({'recipe': recipe.id})
    serializer = serializer(
        data=data, context={'request': request}
    )
    if request.method == "POST":
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            status=status.HTTP_201_CREATED,
            data=self.get_serializer(recipe).data
        )
    model = model_1.objects.filter(
        recipe=recipe, user=request.user
    )
    if not model.exists():
        return Response(
            {'errors': 'В списке нет этого рецепта'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    model.delete()
    return Response(
        {'errors': 'Успешное удаление рецепта'},
        status=status.HTTP_204_NO_CONTENT)
