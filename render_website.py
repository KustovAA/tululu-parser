from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape


if __name__ == '__main__':
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

    server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
    server.serve_forever()
