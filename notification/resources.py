from import_export import resources, fields
from .models import StormEvent

# storm event import resource
# connects csv fields directly into the storm_event model
class StormEventResource(resources.ModelResource):
    event_id = fields.Field(attribute="event_id")
    event_type = fields.Field(attribute="event_type")
    state = fields.Field(attribute="state")
    county = fields.Field(attribute="county")
    begin_year = fields.Field(attribute="begin_year")
    begin_month = fields.Field(attribute="begin_month")
    end_year = fields.Field(attribute="end_year")
    end_month = fields.Field(attribute="end_month")

    class Meta:
        model = StormEvent

        # for bulk situations which is the case here
        use_bulk = True
        batch_size = 5000

        # disable savepoints so remote db does not hang  due to free tier
        use_transactions = False

        # match duplicates by primary key
        import_id_fields = ["event_id"]

        # skip unchanged rows to prevent re-importing same values
        skip_unchanged = True

        # stops idential data from being updated
        skip_diff = True

        # prints warnings 
        report_skipped = True

        # raise import errors to help debugging during development
        raise_errors = True
