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

    return response.text


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


def extract_books_urls(book_page):
    soup = BeautifulSoup(book_page, 'lxml')
    books_url_paths = [
        book.find('a').attrs.get('href') for book in soup.select('.d_book')
    ]
    next_page_url_path = soup.select_one('.npage_select + .npage').attrs.get('href')

    return books_url_paths, next_page_url_path


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
    parser = ArgumentParser(description='Utility downloads books (book text in txt file, and cover) from tululu.org')
    parser.add_argument('--start_page', type=int, default=1, help="id of first book in sequence")
    parser.add_argument('--end_page', type=int, default=2, help="id of last book in sequence")
    parser.add_argument('--dest_folder', type=str, default='./', help="folder of parsed data")
    parser.add_argument('--skip_imgs', type=bool, default=False, help="do not load images")
    parser.add_argument('--skip_txt', type=bool, default=False, help="do not load books")
    parser.add_argument('--json_path', type=str, default='books_data.json', help="json file with results")
    args = parser.parse_args()
    start_page = args.start_page
    end_page = args.end_page
    dest_folder = args.dest_folder
    skip_imgs = args.skip_imgs
    skip_txt = args.skip_txt
    json_path = args.json_path

    next_page_url = f'https://tululu.org/l55/{start_page}'

    parsed_books = []
    current_page = start_page
    while next_page_url and current_page < end_page:
        try:
            book_page = download_book_page(next_page_url)
            books_url_paths, next_page_url_path = extract_books_urls(book_page)
        except (AttributeError, requests.exceptions.HTTPError):
            continue

        books_urls = [urljoin(next_page_url, book_url_path) for book_url_path in books_url_paths]
        next_page_url = urljoin(next_page_url, next_page_url_path)
        current_page += 1

        for book_url in books_urls:
            try:
                book_page = download_book_page(book_url)
                parsed_book = parse_book_page(book_page)
            except (AttributeError, requests.exceptions.HTTPError):
                continue

            img_folder, img_filename = parsed_book['img_path'].split('/')
            book_folder, book_filename = parsed_book['book_path'].split('/')

            if not skip_imgs:
                try:
                    img_filepath = download_file(
                        urljoin(book_url, parsed_book['img_src']),
                        img_filename,
                        os.path.join(dest_folder, img_folder)
                    )
                except requests.exceptions.HTTPError:
                    pass

            if not skip_txt:
                try:
                    book_filepath = download_file(
                        urljoin(book_url, parsed_book['book_src']),
                        book_filename,
                        os.path.join(dest_folder, book_folder),
                        get_content=lambda r: r.text,
                        mode='w'
                    )
                except requests.exceptions.HTTPError:
                    pass

            parsed_books.append(parsed_book)

    os.makedirs(dest_folder, exist_ok=True)
    with open(os.path.join(dest_folder, json_path), "w") as file:
        json.dump(parsed_books, file, ensure_ascii=False)
