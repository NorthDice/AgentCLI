"""Команда rollback для отката изменений."""

import click


@click.command()
@click.option("--steps", default=1, help="Количество шагов для отката")
def rollback(steps):
    """Откатывает последние изменения."""
    click.echo(f"Откат последних {steps} изменений")
    # TODO: Реализовать откат изменений
