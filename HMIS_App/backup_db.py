from django.core.management.base import BaseCommand
import subprocess

class Command(BaseCommand):
    help = "Backup PostgreSQL database"

    def handle(self, *args, **kwargs):
        try:
            subprocess.run([
                'pg_dump',
                '-U', 'postgres',
                '-F', 'c',
                '-h', 'localhost',
                '-p', '5432',
                'Registration',
                '> registration_backup.sql'
            ], check=True, shell=True)

            self.stdout.write(self.style.SUCCESS('Database backup successful!'))

        except subprocess.CalledProcessError as e:
            self.stdout.write(self.style.ERROR(f'Backup failed: {str(e)}'))
