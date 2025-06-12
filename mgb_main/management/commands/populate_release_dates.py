# ваш_app/management/commands/populate_release_dates.py
from django.core.management.base import BaseCommand
from datetime import datetime, date
from users.models import Game


class Command(BaseCommand):
    help = 'Converts first_release_date (timestamp) to release_date (date object) for all games.'

    def handle(self, *args, **options):
        games = Game.objects.all()
        updated_count = 0
        skipped_count = 0
        games_to_bulk_update = []

        self.stdout.write(f"Starting to process {games.count()} games...")

        for game in games:
            if game.first_release_date is not None:
                try:
                    converted_date = datetime.fromtimestamp(game.first_release_date).date()

                    if game.release_date != converted_date:
                        game.release_date = converted_date
                        games_to_bulk_update.append(game)
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(f"Game '{game.name}' (ID: {game.id}): Converted {game.first_release_date} to {game.release_date}."))
                    else:
                        pass

                except (OSError, TypeError, ValueError) as e:
                    self.stderr.write(self.style.ERROR(f"Error converting timestamp for game '{game.name}' (ID: {game.id}), timestamp: {game.first_release_date}. Error: {e}"))
                    if game.release_date is not None:
                        game.release_date = None
                        games_to_bulk_update.append(game)
                    skipped_count += 1
            else:
                if game.release_date is not None:
                    game.release_date = None
                    games_to_bulk_update.append(game)
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f"Game '{game.name}' (ID: {game.id}): first_release_date is None, setting release_date to None."))
                else:
                    pass

        if games_to_bulk_update:
            Game.objects.bulk_update(games_to_bulk_update, ['release_date'])
            self.stdout.write(self.style.SUCCESS(f"Successfully processed and updated {updated_count} games."))
        else:
            self.stdout.write(self.style.NOTICE("No games required an update for release_date."))

        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f"Skipped {skipped_count} games due to invalid or missing timestamps that could not be processed."))