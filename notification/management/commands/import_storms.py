from django.core.management.base import BaseCommand
from import_export.formats.base_formats import CSV
from notification.resources import StormEventResource

# loads storm event csv without using the django admin
# runs as a management command so it will not timeout on railway
class Command(BaseCommand):
    help = "import storm event csv file"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            type=str,
            help="path to csv file to import"
        )

    def handle(self, *args, **options):
        csv_path = options["csv_path"]

        # load import-export resource
        resource = StormEventResource()

        # read csv into dataset
        with open(csv_path, encoding="utf-8") as f:
            dataset = CSV().create_dataset(f.read())

        # import data into database
        result = resource.import_data(dataset, dry_run=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"import completed: {result.total_rows} rows"
            )
        )
