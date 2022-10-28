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
    books_per_page = 10
    pages = list(chunked(books, books_per_page))
    pages_amount = len(pages)
    for page_index, page_books in enumerate(pages, start=1):
        rendered_page = template.render(
            books=page_books,
            pages_amount=pages_amount,
            current_page=page_index
        )

        with open(os.path.join('pages', f'index{page_index}.html'), 'w', encoding="utf8") as file:
            file.write(rendered_page)


if __name__ == '__main__':
    build_page()

    server = Server()
    server.watch('template.html', build_page)
    server.serve(root='.')
