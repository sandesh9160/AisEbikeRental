from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Create default site for Django sites framework'

    def handle(self, *args, **options):
        try:
            # Try to get the site with id=1, or create it
            site, created = Site.objects.get_or_create(
                id=1,
                defaults={
                    'domain': 'localhost:8000' if settings.DEBUG else '123.0.0.1',
                    'name': 'AisEbikeRental'
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created site: {site.domain}')
                )
            else:
                # Update existing site
                site.domain = 'localhost:8000' if settings.DEBUG else '123.0.0.1'
                site.name = 'AisEbikeRental'
                site.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated existing site: {site.domain}')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create site: {str(e)}')
            )

        # List all sites for verification
        sites = Site.objects.all()
        self.stdout.write("All sites:")
        for site in sites:
            self.stdout.write(f"  - {site.id}: {site.domain} ({site.name})")
