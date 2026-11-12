from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Compile the checked-in gettext catalogues without changing their source files."

    def handle(self, *args, **options):
        call_command("compilemessages", verbosity=options["verbosity"])
