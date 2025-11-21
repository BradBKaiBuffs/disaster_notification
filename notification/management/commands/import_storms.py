from django.core.management.base import BaseCommand
from import_export.formats.base_formats import CSV
from notification.resources import StormEventResource

# import the storm event csv
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        # calls StormEventResource
        resource = StormEventResource()

        # build a dataset from the csv
        with open(csv_path, encoding="utf-8") as f:
            dataset = CSV().create_dataset(f.read())

        # import_export each row
        result = resource.import_data(dataset, dry_run=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"{result.total_rows} rows"
            )
        )