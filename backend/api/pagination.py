from rest_framework import pagination


class PageLimitPagination(pagination.PageNumberPagination):
    """Кастомный пагинатор для установки лимита"""
    page_size_query_param = 'limit'
