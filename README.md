# booklead 2.0
Доработанная утилита для загрузки книг из интернет-библиотек  
Первоначальный форк от https://github.com/aliasn3t (уважение ему огромное)

## Поддерживаемые сайты:

* elib.shpl.ru - электронная библиотека ГПИБ
* docs.historyrussia.org - электронная библиотека исторических документов
* prlib.ru - президентская библиотека имени Б.Н. Ельцина
* elibrary.unatlib.ru - национальная электронная библиотека Удмуртской республики
* gwar.mil.ru - информационный портал о первой мировой войне 1914-1918
  ### TO-DO: Добавить еще поддержку:
- https://runivers.ru
- https://elib.omsklib.ru// (библиотека работает очень легко, например [Вот книга в читалке](http://books.omsklib.ru/Knigi/NEW/Viskovatov_Ocherki_Sibir/index.html), и в той же папке и [PDF](http://books.omsklib.ru/Knigi/NEW/Viskovatov_Ocherki_Sibir/Viskovatov_Ocherki_Sibir.pdf) - даже скрипт не нужен
## Добавленные фичи в v2.0: 
- поддержка *prlib.ru*
  - (1-2 секунды страница в качества 3kx2k. Если качество еще больше, то где-то 2-3 сек)
  - индикатор времени
## Добавленные фичи в v2.1: 
- Оптимизирование PDF (в 10-15 раз меньше размер + OCR)  (поддержка пока только для книг с prlib.ru)
  - картинки загружаются в онлайн-архив, и оттуда книга сама оптимизировано конвертируется и проходит OCR. + доступна всем желающим по url. Пример: [здесь](https://archive.org/details/ShturmPragiSuvorovymv1794godu17_/page/n5/mode/2up) с 100 МБ, до 10 + OCR + доступны все другие форматы для чтения
   - *если не нравится мой метод через сервер, можете сами, например, этот локальный [JPEG OPtimizer](https://github.com/XhmikosR/jpegoptim-windows?tab=readme-ov-file) имплементировать (я пробоавл и его, но максимум в 5 раз размер уменьшал без сильной потери качества, а с сервером в 10)*  
- Параллелизирование: добавил возможность параллельно заранить на нескольких корах (соотвественно в n-раз все быстрее загрузиться) [весь вывод в консоль теперь в папке log.txt/multi-thread.log]
- Ускорение: ускорил существующие скачки, например с *elib.shpl.ru*: в среднем на страницу уходило 3-4 сек, сейчас уходит 1/3 сек - где-то в 10 раз быстрее. пробовал еще быстрее, но сервер ошибки выкидывал (ускорение за счёт асинхронного выполнения на каждом коре)

Вид доступных параметров в v2.1:
```
usage: booklead.py [-h] [--pdf y] [--list "list.txt"] [--url "http://..."] [--pause 1.0] [--cores 1] [--continue 0]
                   [--archive 0]

booklead - Загрузчик книг из интернет-библиотек

options:
  -h, --help          show this help message and exit
  --pdf y             Создавать PDF-версии книг
  --list "list.txt"   Файл со списком книг
  --url "http://..."  Ссылка на книгу
  --pause 1.0         Пауза между HTTP-запросами в секундах
  --cores 1           На скольких корах ранить
  --continue 0        Продолжить ли прошлое прерванное скачивание (ссылки в "urls_.txt")? (0/1)
  --archive 0         (0/1) Загрузить ли книгу в Онлайн Архив archive.org (для удобной конвертации и оптимизации + другие тоже имеют доступ по url)
  }
```
Вот пример с archive.org после `--archive 1` [результат](https://archive.org/details/ShturmPragiSuvorovymv1794godu17_). - оптимизированный PDF в 10 раз меньше размер (чем если б сразу тупо картинки в пдф засунули) + OCR + все, кто захочет доступ имеет.

#### Disclaimer про персональные данные и фичу archive.org:  
**Для использования фичи [archive.org](https://archive.org/) нужно вначале зарегаться на сайте, потом ввести свои [access_key;secure_key](https://archive.org/account/s3.php) в спец. файл в скрипте.** Данные ваши никуда не уходят (можете код сами прочекать, или, если не доверяете, просто эту фичу не испльзуйте, я как бы для себя делал, а с вами прост делюсь), чтоб зарегаться можно указать левую почту. access_key;secure_key нужны только для Python API, чтобы файлы на сервер загружать и модифицировать, никакого отношения к вашей "левой" почте- "левому" паролю не имеют. Вот тут рассказано, что это за access/secure key: [archive.org/developers/tutorial-get-ia-credentials.html](https://archive.org/developers/tutorial-get-ia-credentials.html)  
Плюсы сервера, что ваши скачанные книги автоматически будут загружаться и оптимизироваться.   
Когда вы специфицируете `--archive 1`, скрипт вас попросит ввести S3 access key и S3 secret key (оба берутся [отсюда](https://archive.org/account/s3.php) )   
Они будут храниться в файле `personal_data.txt`, он выглядит вот так:
```
xxxxxxxxxxxxxxxx
xxxxxxxxxxxxxxxx
```
Если вам очень нужно, чтобы я их ещё зашифровал, напишите, зашифрую.

### Полезные ресурсы:
- https://help.archive.org/help/how-to-upload-scanned-images-to-make-a-book/
- https://www.loc.gov/marc/umb/um01to06.html
------------

## Запуск (еще протестить)
Все проверял на Python 3.12.10. советую запускать в [virtualenv](https://docs.python.org/3/library/venv.html).  
Для запуска кода потребуется Python с модулями  
`aiohttp==3.9.5
beautifulsoup4==4.13.4   
img2pdf==0.6.1    
internetarchive==5.2.1    
numpy==2.2.5   
opencv_python==4.11.0.86   
Requests==2.31.0   
transliterate==1.10.2`     

Установка модулей: `python -m pip install -r requirements.txt`  
Бинарника нормального пока не сделал. он оч большой получается, 100 МБ, кто умеет делать более оптимизированный, киньте. я пытался через pyinstalller.

## Использование
Открыть консоль в папке со скачанными файлами и чтоб в консоле Python был. Далльше запускать скрипт с параметрами.
Ещё раз параметры в v2.1:
```
usage: python booklead.py [-h] [--pdf y] [--list "list.txt"] [--url "http://..."] [--pause 1.0] [--cores 1] [--continue 0]
                   [--archive 0]

booklead - Загрузчик книг из интернет-библиотек

options:
  -h, --help          show this help message and exit
  --pdf y             Создавать PDF-версии книг
  --list "list.txt"   Файл со списком книг
  --url "http://..."  Ссылка на книгу
  --pause 1.0         Пауза между HTTP-запросами в секундах
  --cores 1           На скольких корах ранить
  --continue 0        Продолжить ли прошлое прерванное скачивание (ссылки в "urls_.txt")? (0/1)
  --archive 0         (0/1) Загрузить ли книгу в Онлайн Архив archive.org (для удобной конвертации и оптимизации + другие тоже имеют доступ по url)
  }
```

`--list` загрузка книг по ссылкам из файла  
Пример использования: `python booklead.py --list books.txt`  
Пример содержимого **books.txt**:  
```
https://www.prlib.ru/item/420931
http://docs.historyrussia.org/ru/nodes/139435
...
http://elib.shpl.ru/ru/nodes/16533-vyp-1-zhilischnoe-stroitelstvo-v-gorodskih-poseleniyah-rsfsr-ukrainskoy-ssr-i-belorusskoy-ssr-1927
```
`--url` загрузка одной книги по ссылке  
Пример использования: `python booklead.py --url https://www.prlib.ru/item/420931`  
`--pdf` создание PDF-версий загружаемых книг  
Пример использования: `python booklead.py --list books.txt --pdf y`  
`--cores` -ск-ко коров ранить, пример: `python booklead.py --list books.txt --cores 10` Начнет грузить книги с `books.txt` на 10 корах. Если у вас 10 книг в папке и книги +- одного размера, то в 10 раз быстрее закончится закачка.  
`--continue` - для продолжения прерванного прошлого скачивания  
`--archive` - загрузит книги на сервер archive.org (вначале вас попросит коды, если их еще нет). Использование: `python booklead.py --list books.txt --cores 10 --archive 1` -Все 10 книг будут архивироваться на сервер. Чтобы их просмотреть зайдите на свой аккаунт и My Uploads, все они там будут где-то через 5 минут после закачки (серверу требуется время обработать)
