from django.contrib.auth import update_session_auth_hash
from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from recipes.models import (Favourite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingList, Tag)
from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from users.models import Subscribtions, User

from .add_and_del import add_and_del
from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrAdminOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeGetSerializer, RecipePostSerializer,
                          RecipeShortSerializer, ShoppingCartSerializer,
                          SubscriptionSerializer, TagSerializer,
                          UserGetSerializer, UserPostSerializer,
                          UserWithRecipesSerializer)


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
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = IngredientFilter


class TagViewSet(ReadOnlyModelViewSet):
    """Обработка операций с тегами"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    """Обработка операций связанная с рецептами"""
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrAdminOrReadOnly]
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination

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
        return add_and_del(
            self, request,
            FavoriteSerializer, Favourite, **kwargs
        )

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, **kwargs):
        return add_and_del(
            self, request,
            ShoppingCartSerializer, ShoppingList, **kwargs
        )

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping__user=user).values(
            name=F('ingredient__name'),
            measurement_unit=F('ingredient__measurement_unit')).annotate(
            number=Sum('amount')
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
