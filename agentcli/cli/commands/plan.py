"""Команда plan для создания плана действий."""

import click


@click.command()
@click.argument("query", required=True)
def plan(query):
    """Создает план действий на основе запроса.
    
    QUERY - запрос на естественном языке для создания плана.
    """
    click.echo(f"План действий для запроса: {query}")
    # TODO: Реализовать создание плана
