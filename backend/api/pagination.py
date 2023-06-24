from django.core import paginator
from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    django_paginator_class = paginator.Paginator
    page_size_query_param = 'limit'
    page_size = 6
