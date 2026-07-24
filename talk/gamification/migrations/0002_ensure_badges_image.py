from django.db import migrations


def ensure_badges_image_column(apps, schema_editor):
    Badge = apps.get_model('gamification', 'Badges')
    table = Badge._meta.db_table
    columns = {
        column.name for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(), table
        )
    }
    if 'image' not in columns:
        schema_editor.add_field(Badge, Badge._meta.get_field('image'))


class Migration(migrations.Migration):
    dependencies = [
        ('gamification', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ensure_badges_image_column, migrations.RunPython.noop),
    ]
