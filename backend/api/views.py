from .pagination import PageLimitPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (
    UserWithRecipesSerializer, UserGetSerializer, UserPostSerializer,
    RecipeGetSerializer, IngredientSerializer, TagSerializer,
    RecipeShortSerializer, RecipePostSerializer, SubscriptionSerializer,
    ShoppingCartSerializer, FavoriteSerializer
)
from .filters import RecipeFilter
from django.db.models import F, Sum
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework import filters
from users.models import User, Subscribtions
from django.http import HttpResponse
from recipes.models import (
    Ingredient, Tag, Recipe, Favourite,
    ShoppingList, IngredientInRecipe
)
from rest_framework import viewsets, status, mixins
from djoser.serializers import SetPasswordSerializer
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import get_object_or_404


# Применю миксины для удобства управления пользователями
class CustomUserViewSet(
        mixins.CreateModelMixin, mixins.ListModelMixin,
        mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    pagination_class = PageLimitPagination

    def get_instance(self):
        return self.request.user

    # прописываю какие функции выполняются при том или ином запросе
    def get_serializer_class(self):
        if self.action in ['subscriptions', 'subscribe']:
            return UserWithRecipesSerializer
        elif self.request.method == 'GET':
            return UserGetSerializer
        elif self.request.method == 'POST':
            return UserPostSerializer

    # Добавляю условие доступа
    def get_permissions(self):
        if self.action == 'retrieve':
            self.permission_classes = [IsAuthenticated]
        return super(self.__class__, self).get_permissions()

    # Get на me только зарегистрированным пользователям
    @action(detail=False, permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        self.get_object = self.get_instance
        return self.retrieve(request, *args, **kwargs)

    # Post запрос на изменение пароля
    @action(["POST"], detail=False, permission_classes=[IsAuthenticated])
    def set_password(self, request, *args, **kwargs):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.request.user.set_password(serializer.data['new_password'])
        self.request.user.save()
        update_session_auth_hash(self.request, self.request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Запрос с подписками
    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        users = User.objects.filter(
            following__user=request.user
        ).prefetch_related('recipes')
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True,
                context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = UserWithRecipesSerializer(
            users, many=True, context={'request': request}
        )
        return Response(UserWithRecipesSerializer(
            users, many=True, context={'request': request}
        ).data)

    # Отписаться подписаться на пользователя
    @action(
        ["POST", "DELETE"],
        detail=True,
        permission_classes=[IsAuthorOrAdminOrReadOnly],
    )
    def subscribe(self, request, **kwargs):
        user = get_object_or_404(User, id=kwargs['pk'])
        data = request.data.copy()
        data.update({'author': user.id})
        serializer = SubscriptionSerializer(
            data=data, context={'request': request}
            )
        if request.method == "POST":
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                status=status.HTTP_201_CREATED,
                data=self.get_serializer(user).data
            )

        else:
            subscription = Subscribtions.objects.filter(
                author=user, user=request.user
            )
            if not subscription.exists():
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            subscription.delete()
            return Response(
                {'errors': 'Успешная отписка'},
                status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(ReadOnlyModelViewSet):
    """Обработка операций с ингредиентами"""
    # Беру все ингредиенты в обработку
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    # нужно проверить
    search_fields = ('^name',)


class TagViewSet(ReadOnlyModelViewSet):
    """Обработка операций с тегами"""
    # Беру все ингредиенты в обработку
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Обработка операций связанная с рецептами"""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination

    # Выбор сериализатора в зависимости от метода
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeGetSerializer
        elif self.action in ['favorite', 'shopping_cart', ]:
            return RecipeShortSerializer
        return RecipePostSerializer

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, **kwargs):
        recipe = get_object_or_404(Recipe, id=kwargs['pk'])
        data = request.data.copy()
        data.update({'recipe': recipe.id})
        serializer = FavoriteSerializer(
            data=data, context={'request': request}
            )
        if request.method == "POST":
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                status=status.HTTP_201_CREATED,
                data=self.get_serializer(recipe).data
            )
        else:
            favorite = Favourite.objects.filter(
                recipe=recipe, user=request.user
            )
            if not favorite.exists():
                return Response(
                    {'errors': 'В списке избранного нет этого рецепта'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            favorite.delete()
            return Response(
                {'errors': 'Успешное удаление рецепта из избранного'},
                status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, **kwargs):
        recipes = get_object_or_404(Recipe, id=kwargs['pk'])
        data = request.data.copy()
        data.update({'recipe': recipes.id})
        serializer = ShoppingCartSerializer(
            data=data, context={'request': request}
            )
        if request.method == "POST":
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                status=status.HTTP_201_CREATED,
                data=self.get_serializer(recipes).data
            )
        else:
            shopping = ShoppingList.objects.filter(
                recipe=recipes, user=request.user
            )
            if not shopping.exists():
                return Response(
                    {'errors': 'В списке корзины нет этого рецепта'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            shopping.delete()
            return Response(
                {'errors': 'Успешное удаление рецепта из корзины'},
                status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=user).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')).annotate(
            amount=Sum('amount')
        )
        data = []
        for ingredient in ingredients:
            data.append(
                f'{ingredient["name"]} - '
                f'{ingredient["amount"]} '
                f'{ingredient["measurement_unit"]}'
            )
        content = 'Список покупок:\n\n' + '\n'.join(data)
        filename = 'Shopping_cart.txt'
        request = HttpResponse(content, content_type='text/plain')
        request['Content-Disposition'] = f'attachment; filename={filename}'
        return request
