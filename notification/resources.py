from import_export import resources, fields
from .models import StormEvent

# storm event import resource that links csv fields to storm_event model
class StormEventResource(resources.ModelResource):
    event_id = fields.Field(attribute="event_id", column_name="EVENT_ID")
    event_type = fields.Field(attribute="event_type", column_name="EVENT_TYPE")
    state = fields.Field(attribute="state", column_name="STATE")
    county = fields.Field(attribute="county", column_name="CZ_NAME")
    begin_year = fields.Field(attribute="begin_year", column_name="BEGIN_YEAR")
    begin_month = fields.Field(attribute="begin_month", column_name="BEGIN_MONTH")
    end_year = fields.Field(attribute="end_year", column_name="END_YEAR")
    end_month = fields.Field(attribute="end_month", column_name="END_MONTH")
    begin_time = fields.Field(attribute="begin_time", column_name="BEGIN_TIME")
    end_time = fields.Field(attribute="end_time", column_name="END_TIME")''
    # added to account for area_desc issue, using fips to link to county/state
    county_fips = fields.Field(attribute="county_fips", column_name="CZ_FIPS")
    state_fips = fields.Field(attribute="state_fips", column_name="STATE_FIPS")

    class Meta:
        model = StormEvent

        # for bulk situations which is the case here
        use_bulk = True
        batch_size = 5000

        # disable savepoints so remote db does not hang  due to free tier
        use_transactions = False

        # match duplicates by primary key
        import_id_fields = ["event_id"]

        # skips duplicates
        skip_unchanged = True
        skip_diff = True

        # for debugging
        raise_errors = True
