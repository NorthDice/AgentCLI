"""Команда search для поиска в проекте."""

import click


@click.command()
@click.argument("query", required=True)
@click.option("--path", default=".", help="Путь для поиска")
def search(query, path):
    """Выполняет поиск по файлам проекта.
    
    QUERY - строка или регулярное выражение для поиска.
    """
    click.echo(f"Поиск '{query}' в {path}")
    # TODO: Реализовать поиск
