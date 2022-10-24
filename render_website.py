import json
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def build_page():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('template.html')
    with open(os.path.join('parsed', 'books_data.json'), 'r') as file:
        books = json.load(file)

    os.makedirs('pages', exist_ok=True)
    pages_amount = 5
    for chunk_index, chunk in enumerate(chunked(books, pages_amount), start=1):
        rendered_page = template.render(
            books=chunk,
            pages_amount=pages_amount,
            current_page=chunk_index
        )

        with open(os.path.join('pages', f'index{chunk_index}.html'), 'w', encoding="utf8") as file:
            file.write(rendered_page)


if __name__ == '__main__':
    build_page()

    server = Server()
    server.watch('template.html', build_page)
    server.watch('static/styles.css', build_page)
    server.serve(root='.')
