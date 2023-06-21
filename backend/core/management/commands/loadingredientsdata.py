from csv import DictReader

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает объекты и таблиц csv в БД.'

    def handle(self, *args, **kwargs):

        for row in DictReader(open('data/ingredients.csv', encoding="utf8")):
            ingridient = Ingredient(
                name=row['name'],
                measurement_unit=row['measurement_unit']
            )
            ingridient.save()
        self.stdout.write('Объекты загруженны в базу данных.')
