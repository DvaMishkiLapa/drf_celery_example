from django.db import migrations


def create_default_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.get_or_create(domain='localhost', defaults={'name': 'localhost'})
    Site.objects.get_or_create(domain='app', defaults={'name': 'app'})


def remove_default_site(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    Site.objects.filter(domain__in={'localhost', 'app'}).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique')
    ]

    operations = [
        migrations.RunPython(create_default_site, reverse_code=remove_default_site),
    ]
