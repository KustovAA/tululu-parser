import json
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server


def build_page():
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('template.html')
    with open(os.path.join('parsed', 'books_data.json'), 'r') as file:
        books = json.load(file)

    rendered_page = template.render(
        books=books
    )

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


if __name__ == '__main__':
    build_page()

    server = Server()
    server.watch('template.html', build_page)
    server.serve(root='.')
