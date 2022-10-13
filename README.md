# Парсер книг с сайта tululu.org

Консольная утилита скачивает информацию о книгах
Информация о книге:
* Текст книги в формате txt
* Автор книги
* Название книги
* Обложка книги
* Комментарии к книге на tululu.org
* Жанры книги

### Как установить

Необходимо установить python версии 3.10. Далее
* ```python -m venv env```
* ```source env/bin/activate```
* ```pip intall poetry```
* ```poetry intall```

### Аргументы

* `--start_id` - id первой страницы
* `--end_id` - id последней страницы
* `--dest_folder` - путь к каталогу с результатами парсинга: картинкам, книгам, JSON
* `--skip_imgs` - не скачивать картинки
* `--skip_txt` - не скачивать книги
* `--json_path` - указать свой путь к *.json файлу с результатами

### Как запускать

```python main.py --start_id=<start_id> --end_id=<end_id> --dest_folder=<dest_folder> --skip_imgs=<skip_imgs> --skip_txt=<skip_txt> --json_path=<json_path>```
