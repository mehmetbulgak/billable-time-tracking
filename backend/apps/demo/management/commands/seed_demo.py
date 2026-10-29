from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Role
from apps.demo.catalog import DEMO_PASSWORD, MEMBERS
from apps.demo.seeding import ORGANIZATION_SLUG, DemoSeeder
from apps.organizations.models import Organization


class Command(BaseCommand):
    help = "Creates the Northwind Studio demo agency with clients, contracts, time and invoices."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the existing demo agency before seeding.",
        )
        parser.add_argument("--seed", type=int, default=42, help="Random seed for repeatable data.")

    def handle(self, *args: Any, **options: Any) -> None:
        exists = Organization.objects.filter(slug=ORGANIZATION_SLUG).exists()
        if exists and not options["reset"]:
            raise CommandError("Demo data already exists. Run with --reset to recreate it.")

        report = DemoSeeder(seed=options["seed"]).run(reset=options["reset"])

        self.stdout.write(self.style.SUCCESS("Demo agency created."))
        self.stdout.write(
            f"{report.members} members, {report.clients} clients, {report.projects} projects, "
            f"{report.time_entries} time entries, {len(report.invoices)} invoices.",
        )
        for line in report.invoices:
            self.stdout.write(f"  {line}")
        self.stdout.write("\nPublic demo accounts:")
        for member in MEMBERS:
            if member.role == Role.OWNER:
                continue
            self.stdout.write(f"  {member.email} ({member.role.label})")
        self.stdout.write(f"Password: {DEMO_PASSWORD}")
