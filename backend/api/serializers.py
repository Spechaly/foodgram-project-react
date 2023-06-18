import base64
from djoser.serializers import UserSerializer, UserCreateSerializer
from rest_framework import serializers
from django.contrib.auth.models import AnonymousUser
from users.models import User, Subscribtions
from recipes.models import (
    Recipe, Ingredient, Tag, IngredientInRecipe,
    Favourite, ShoppingList
)
from rest_framework.exceptions import ValidationError
from rest_framework import status
from django.core.files.base import ContentFile


class Base64ImageField(serializers.ImageField):
    """Сериализатор для декодирования картинок"""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserGetSerializer(UserSerializer):
    """Сераализация для просмотра профилей пользователей"""

    # Согласно Redoc, должно быть поле подписок, только для чтения
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        # Использую модель юзера
        model = User
        # выбираю все доступные для модели юзера значения + подписки
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
        )

    # функция проверки подписки, если нет False, иначе True
    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if isinstance(user, AnonymousUser):
            return False
        return Subscribtions.objects.filter(user=user, author=obj).exists()


class UserPostSerializer(UserCreateSerializer):
    """Сериализатор создания пользователя"""

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class UserWithRecipesSerializer(UserGetSerializer):
    """Сериализатор для пользователя c рецептами"""

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def validate(self, data):
        author = self.instance
        user = self.context.get('request').user
        if Subscribtions.objects.filter(author=author, user=user).exists():
            raise ValidationError(
                detail='Вы уже подписаны на этого пользователя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        if user == author:
            raise ValidationError(
                detail='Нельзя подписаться на самого себя!',
                code=status.HTTP_400_BAD_REQUEST
            )
        return data

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if isinstance(user, AnonymousUser):
            return False
        return Subscribtions.objects.filter(user=user, author=obj).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return RecipeShortSerializer(recipes, many=True, read_only=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class RecipeShortSerializer(serializers.ModelSerializer):
    '''Сериализатор для отображения краткой информации о рецептах'''

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента"""

    class Meta:
        model = Ingredient
        # берем все поля модели
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов"""

    class Meta:
        model = Tag
        # берем все поля модели
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок"""
    user = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = Subscribtions
        fields = ('author', 'user')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Subscribtions.objects.all(),
                fields=['author', 'user'],
                message="Вы уже подписаны на этого пользователя"
            )
        ]

    def create(self, validated_data):
        return Subscribtions.objects.create(
            user=self.context.get('request').user, **validated_data)

    def validate_author(self, value):
        if self.context.get('request').user == value:
            raise serializers.ValidationError({
                'errors': 'Подписка на самого себя не возможна!'
            })
        return value


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов в рецептах"""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient.id'
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeGetSerializer(serializers.ModelSerializer):
    '''Сериализатор для модели Recipe. Для get /recipes/ и /recipes/id/'''
    tags = TagSerializer(many=True, read_only=True)
    author = UserGetSerializer()
    ingredients = IngredientInRecipeSerializer(
        source='IngredientsInRecipe',
        many=True,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False

        return Favourite.objects.filter(recipe=obj, user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False

        return ShoppingList.objects.filter(
            recipe=obj, user=request.user
        ).exists()


class RecipePostSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецептов."""
    author = UserGetSerializer(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = IngredientInRecipeSerializer(
        source='IngredientsInRecipe',
        many=True,
    )
    image = Base64ImageField(
        required=False,
        allow_null=True
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time'
        )

    @staticmethod
    def save_ingredients(recipe, ingredients):
        ingredients_list = []
        for ingredient in ingredients:
            current_ingredient = ingredient['ingredient']['id']
            current_amount = ingredient.get('amount')
            ingredients_list.append(
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=current_ingredient,
                    amount=current_amount
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredients_list)

    def validate(self, data):
        cooking_time = data.get('cooking_time')
        if cooking_time <= 0:
            raise serializers.ValidationError(
                {
                    'error': 'Время приготовления не должно быть менее 1 мин.'
                }
            )
        ingredients_list = []
        ingredients_in_recipe = data.get('IngredientsInRecipe')
        for ingredient in ingredients_in_recipe:
            if ingredient.get('amount') <= 0:
                raise serializers.ValidationError(
                    {
                        'error': 'Ингредиентов не должно быть менее одного.'
                    }
                )
            ingredients_list.append(ingredient['ingredient']['id'])
        if len(ingredients_list) > len(set(ingredients_list)):
            raise serializers.ValidationError(
                {
                    'error': 'Ингредиенты в рецепте не должны повторяться.'
                }
            )
        return data

    def create(self, validated_data):
        author = self.context.get('request').user
        ingredients = validated_data.pop('IngredientsInRecipe')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data, author=author)
        recipe.tags.add(*tags)
        self.save_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        ingredients = validated_data.pop('IngredientsInRecipe')
        tags = validated_data.pop('tags')
        instance.tags.clear()
        instance.tags.add(*tags)
        instance.ingredients.clear()
        recipe = instance
        self.save_ingredients(recipe, ingredients)
        instance.save()
        return instance

    def to_representation(self, instance):
        serializer = RecipeGetSerializer(
            instance,
            context={'request': self.context.get('request')}
        )
        return serializer.data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для избранных рецептов."""
    user = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True,
    )

    class Meta:
        model = Favourite
        fields = ('recipe', 'user', )
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Favourite.objects.all(),
                fields=['recipe', 'user', ],
                message='Этот рецепт уже добавлен в избранное.'
            )
        ]

    def create(self, validated_data):
        return Favourite.objects.create(
            user=self.context.get('request').user, **validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""
    user = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    recipe = serializers.PrimaryKeyRelatedField(
        queryset=Recipe.objects.all(),
        write_only=True,
    )

    class Meta:
        model = ShoppingList
        fields = ('recipe', 'user',)
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(),
                fields=['recipe', 'user', ],
                message='Этот рецепт уже добавлен в список покупок.'
            )
        ]

    def create(self, validated_data):
        return ShoppingList.objects.create(
            user=self.context.get('request').user, **validated_data)
