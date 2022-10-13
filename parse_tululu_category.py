from argparse import ArgumentParser
import json
from urllib.parse import urljoin, unquote, urlencode
import os

from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
import requests
from retry import retry


def check_for_redirect(response):
    if response.is_permanent_redirect or response.is_redirect:
        raise requests.exceptions.HTTPError


@retry(exceptions=requests.exceptions.ConnectionError, delay=1, backoff=2, tries=10)
def download_book_page(url):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()
    check_for_redirect(response)

    return response


@retry(exceptions=requests.exceptions.ConnectionError, delay=1, backoff=2, tries=10)
def download_file(
    url,
    filename,
    folder,
    get_content=lambda r: r.content,
    mode='wb'
):
    response = requests.get(url, allow_redirects=False)
    response.raise_for_status()

    check_for_redirect(response)
    filepath = os.path.join(folder, sanitize_filename(filename))

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, mode) as file:
        file.write(get_content(response))

    return filepath


def download_txt(url, filename, folder='books/'):
    return download_file(
        url,
        filename,
        folder,
        get_content=lambda r: r.text,
        mode='w'
    )


def download_image(url, filename, folder='images/'):
    return download_file(url, filename, folder)


def get_books_urls(url):
    response = download_book_page(url)

    soup = BeautifulSoup(response.text, 'lxml')
    books_urls = [
        urljoin(url, book.find('a').attrs.get('href')) for book in soup.select('.d_book')
    ]
    next_page_url = urljoin(url, soup.select_one('.npage_select + .npage').attrs.get('href'))

    return books_urls, next_page_url


def parse_book_page(page):
    soup = BeautifulSoup(page, 'lxml')
    title, author = [item.strip() for item in soup.find('h1').text.split('::')]
    comments = [comment.text for comment in soup.select('.texts .black')]
    genres = [genre.text for genre in soup.select_one('.d_book:-soup-contains("Жанр книги:")').find_all('a')]
    img = soup.find(class_='bookimage').find('img').attrs.get('src')
    book_src = soup.select_one('a:-soup-contains("скачать txt")').attrs.get('href')

    return {
        'title': title,
        'author': author,
        'book_path': os.path.join('books', f'{title}.txt'),
        'book_src': book_src,
        'comments': comments,
        'genres': genres,
        'img_path': os.path.join('images', unquote(img).split('/')[-1]),
        'img_src': img,
    }


if __name__ == '__main__':
    next_page_url = f'https://tululu.org/l55/'

    i = 0
    while next_page_url is not None and i < 1:
        books_urls, next_page_url = get_books_urls(next_page_url)
        i += 1

        parsed_books = []
        for book_url in books_urls:
            try:
                parsed_book = parse_book_page(download_book_page(book_url).text)
                img_folder, img_filename = parsed_book['img_path'].split('/')
                book_folder, book_filename = parsed_book['book_path'].split('/')
                img_filepath = download_image(urljoin(book_url, parsed_book['img_src']), img_filename, img_folder)
                book_filepath = download_txt(urljoin(book_url, parsed_book['book_src']), book_filename, book_folder)
                parsed_books.append(parsed_book)
            except AttributeError:
                pass

        books_data = json.dumps(parsed_books, ensure_ascii=False).encode('utf8')
        with open("books_data.json", "w") as file:
            file.write(books_data.decode())
