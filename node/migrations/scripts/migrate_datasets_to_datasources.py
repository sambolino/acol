import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")  # adjust if needed
django.setup()

from node.models import DataSet, DataSource

groups = {}

for ds in DataSet.objects.all():
    source_ids = tuple(sorted(ds.sources.values_list("id", flat=True)))

    key = source_ids

    if key not in groups:
        datasource = DataSource.objects.create(
            description=ds.description
        )
        datasource.sources.set(ds.sources.all())
        groups[key] = datasource
    else:
        datasource = groups[key]

    if ds.collision_id:
        datasource.collisions.add(ds.collision)

print("Created %s DataSource objects from %s DataSet objects" % (
    len(groups),
    DataSet.objects.count()
))
