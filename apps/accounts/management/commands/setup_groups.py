from django.core.management.base import BaseCommand

from apps.accounts.services import ensure_default_role_groups


class Command(BaseCommand):
    help = "Create or update default RBAC role groups without removing custom permissions."

    def handle(self, *args, **options):
        ensure_default_role_groups()
        self.stdout.write(self.style.SUCCESS("Default role groups synchronized."))
