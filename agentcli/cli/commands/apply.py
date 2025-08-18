"""Команда apply для выполнения плана действий."""

import click


@click.command()
@click.argument("plan_file", type=click.Path(exists=True), required=True)
def apply(plan_file):
    """Выполняет план действий из файла.
    
    PLAN_FILE - путь к файлу плана (JSON/YAML).
    """
    click.echo(f"Выполнение плана из файла: {plan_file}")
    # TODO: Реализовать выполнение плана
