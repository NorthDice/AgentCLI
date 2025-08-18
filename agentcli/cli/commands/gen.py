"""Команда gen для генерации кода."""

import click


@click.command()
@click.argument("description", required=True)
@click.option("--output", "-o", help="Путь к выходному файлу")
def gen(description, output):
    """Генерирует код на основе описания.
    
    DESCRIPTION - описание кода для генерации.
    """
    click.echo(f"Генерация кода по описанию: {description}")
    if output:
        click.echo(f"Вывод в файл: {output}")
    # TODO: Реализовать генерацию кода
