# -*- coding: utf-8 -*-
import argparse
import json
import os
import re
import urllib.parse
import asyncio
from aiohttp import ClientSession
import datetime
import numpy as np
import nest_asyncio
from util import CV2_Russian, BinaryToDecimal,number_of_images, Postprocess, Time_Processing
import cv2
import random
import img2pdf
from bs4 import BeautifulSoup
import sys
from util import get_logger
from util import md5_hex, to_float, cut_bom, perror, progress, ptext, safe_file_name, Browser, select_one_text_optional
from util import select_one_text_required, select_one_attr_required, gwar_fix_json,mkdirs_for_regular_file
from util import user_agents

log = get_logger(__name__)

BOOK_DIR = 'books'

eshplDl_params = {
    'quality': 8,
    'ext': 'jpg'
}

prlDl_params = {
    'ext': 'jpg' }
 

bro: Browser


def makePdf(pdf_path, img_folder, img_ext):
    img_list = []
    for r, _, ff in os.walk(img_folder):
        for fname in ff:
            if fname.endswith(f'.{img_ext}'):
                img_list.append(os.path.join(r, fname))
    img_list.sort()
    pdf = img2pdf.convert(img_list)
    with open(pdf_path, "wb") as fd:
        fd.write(pdf)


def saveImage(url, img_id, folder, ext, referer):
    image_short = '%05d.%s' % (img_id, ext)
    image_path = os.path.join(BOOK_DIR, folder, image_short)
    headers = {'Referer': referer}
    expected_ct = re.compile('image/')
    bro.download(url, image_path, headers, content_type=expected_ct, skip_if_file_exists=True)



async def fetch_image(url: str, i,queue, headers):
    """ Не добавляйте в util.py, у меня тогда asyncio не работал (может баг на моей стороне)
    по url скачиваю картинку и добавляю в binary в queue asyncio
    """
    async with ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            result = (i, await response.read())
            await queue.put(result)
            
async def async_images(url,num,headers):
    """Не добавляйте в util.py, у меня тогда asyncio не работал (может баг на моей стороне)
    call every tile image to download in async mode (in the end, add binary with the image number to results_prlDl
    """

    queue = asyncio.Queue()
    async with asyncio.TaskGroup() as group:
        for i in range(num):
            group.create_task(fetch_image(url.format(i), i,queue,headers))
    global results_prlDl
    results_prlDl=[]
    while not queue.empty():
        results_prlDl.append(await queue.get())


def eshplDl(url):
    ext = eshplDl_params['ext']
    quality = eshplDl_params['quality']
    domain = urllib.parse.urlsplit(url).netloc

    html_text = bro.get_text(url)
    
    soup = BeautifulSoup(html_text, 'html.parser')
    title = select_one_text_optional(soup, 'title') or md5_hex(url)
    title = safe_file_name(title)
    
    for script in soup.findAll('script'):
        
        
        st = str(script)
        
        if 'initDocview' in st:
            book_json = json.loads(st[st.find('{"'): st.find(')')])
    ptext(f' Каталог для загрузки: {title}')
    pages = book_json['pages']
    for idx, page in enumerate(pages):
        img_url = f'http://{domain}/pages/{page["id"]}/zooms/{quality}'
        saveImage(img_url, idx + 1, title, ext, url)
        progress(f'  Прогресс: {idx + 1} из {len(pages)} стр.')
    return title, ext
    

def prlDl(url):
    """
    Президентская библиотека имени Б.Н. Ельцина
    Формат - серия изображений
    Пример урла книги (HTML) - https://www.prlib.ru/item/420931
    """
    ext = prlDl_params['ext']
    html_text = bro.get_text(url)
    soup = BeautifulSoup(html_text, 'html.parser')
    title = select_one_text_optional(soup, 'h1') or md5_hex(url)
    title = safe_file_name(title)
    ptext(f'Каталог для загрузки: {title}')
    
    for script in soup.find_all('script'): #findAll deprecated
        st = str(script)
        if 'jQuery.extend' in st:
            book_json = json.loads(st[st.find('{"'): st.find(');')])
            if "item" in url.split("prlib.ru/")[1]:   #case for https://www.prlib.ru/item/*** 
                book = book_json['diva']['1']['options']
            elif "node" in url.split("prlib.ru/")[1]:     #case for https://www.prlib.ru/node/***
                book = book_json['diva']['settings']
    json_text = bro.get_text(book['objectData'])
    book_data = json.loads(json_text)
    pages = book_data['pgs']
    num_of_pages_down=0 #for the time prediction
    start=datetime.datetime.now()#for the time prediction
    headers = {'Referer': url}
    for idx, page in enumerate(pages):
        
        img_url = 'https://content.prlib.ru/fcgi-bin/iipsrv.fcgi?FIF={}/{}&JTL={},'.format(
            book['imageDir'], page['f'], page['m']) #поменял здесь немного вид урл, так как по частям качаю
        # брал урл отсюда: https://iipimage.sourceforge.io/documentation/protocol
        img_url+="{}"
        width, height=number_of_images(page["d"][len(page['d']) - 1]['w'],page["d"][len(page['d']) - 1]['h'])
        
        image_short = '%05d.%s' % (idx+1, ext)
        image_path = os.path.join(BOOK_DIR, title, image_short)

        # заменяю все фичи ручками (например тут skip_if_exists), которые были ранее доступны через функции 
        #(т.к. метод у меня скачивания немного другой)
        if os.path.exists(image_path) and os.stat(image_path).st_size > 0:
            log.info(f'Пропускаю скачанный файл: {image_path}')
            progress(f'  Прогресс: {idx + 1} из {len(pages)} стр. ')
        else: 
            mkdirs_for_regular_file(image_path)
            #nest_asyncio.apply() # нужен только чтобы async работал нормально в Jupyter ( https://pypi.org/project/nest-asyncio/)
            # получить все данные с картиники
            headers.update({'User-Agent': random.choice(user_agents)})
            asyncio.run(async_images(img_url,width*height,headers))

            global results_prlDl
            # просессить все данные и в конце вывести картинку
            Postprocess(results_prlDl,width,height, image_path)
            
            # Time Formatting/Prediction:
            prog=datetime.datetime.now()-start
            num_of_pages_down+=1
            left=prog/num_of_pages_down*(len(pages)-(idx+1)) #based on the values before prediction
            minutes, seconds = Time_Processing(left)
            past_min, past_sec=Time_Processing(prog)
            progress(f'  Прогресс: {idx + 1} из {len(pages)} стр. | Прошло (мин:сек): {past_min}:{past_sec:02d} ;Осталось: {minutes}:{seconds:02d} ')
    return title, ext


def unatlib_download(url):
    """
    Национальная электронная библиотека Удмуртской республики
    Формат - PDF
    Пример урла книги (HTML) - https://elibrary.unatlib.ru/handle/123456789/18116
    Пример урла книги (PDF) - https://elibrary.unatlib.ru/bitstream/handle/123456789/18116/uiiyl_book_075.pdf
    Реферером должен быть https://elibrary.unatlib.ru/build/pdf.worker.js
    """
    html_text = bro.get_text(url)
    soup = BeautifulSoup(html_text, 'html.parser')
    title = select_one_text_required(soup, 'title') or md5_hex(url)
    title = safe_file_name(title)
    pdf_href = select_one_attr_required(soup, '#dsview', 'href')
    pdf_url = f'https://elibrary.unatlib.ru{pdf_href}'
    headers = {'Referer': 'https://elibrary.unatlib.ru/build/pdf.worker.js'}
    pdf_file = os.path.join(BOOK_DIR, f'{title}.pdf')
    bro.download(pdf_url, pdf_file, headers, skip_if_file_exists=True)
    return None  # all done, no further action needed


def gwarDL(url): 
    """
    Первая мировая война 1914-1918 - Информационный портал
    Формат - серия изображений/PDF
    Пример урла type 1 (HTML) - https://gwar.mil.ru/heroes/document/50000001/
    Пример урла type 2 (HTML) - https://gwar.mil.ru/documents/view/?id=88000899 или https://gwar.mil.ru/documents/view/88009650/
    Пример урла type 3 (PDF) - https://gwar.mil.ru/books/105501406
    """
    ext = 'jpg' # пока так
    json_url = ''
    request_data = {}

    html_text = bro.get_text(url)
    soup = BeautifulSoup(html_text, 'html.parser')

    title = select_one_text_required(soup, 'title') or md5_hex(url)
    title = safe_file_name(title)

    for script in soup.findAll('script'):
        st = str(script)
        if 'var parentId' in st: # type 1
            page_json = st[st.find('{'): st.find(';\n</')]
            page_json_fix = gwar_fix_json(page_json, True)
            book_id = page_json_fix['id']
            boxes_id = page_json_fix['documents_pages']['deals_boxes_id']

            request_data = {
                "indices": ["gwar"],
                "entities": ["stranitsa"],
                "queryFields": {
                    "deal_box_id": boxes_id
                    },
                "from": 0,
                "size": 3000,
                "builderType": "HeroesStranitsa"
                }
            
            json_url = 'https://gwar.mil.ru/gt_data/?builder=HeroesStranitsa'
        elif 'var documentjs' in st: # type 2
            page_json = st[st.find('{\''): st.find('</script>')]
            page_json_fix = gwar_fix_json(page_json)
            book_id = page_json_fix['id']

            if (page_json_fix['hits']['hits'][0]['_type'] == 'document'):
                query_fields = {
                    "document_id": book_id,
                    }
            elif (page_json_fix['hits']['hits'][0]['_type'] == 'deal'):
                query_fields = {
                    "document_id": book_id,
                    "deal_box_id": book_id
                    }

            request_data = {
                "indices": "gwar_document",
                "entities": "document_image",
                "queryFields": query_fields,
                "from": 0,
                "size": 10000,
                "builderType": "DocumentView"
                }

            json_url = 'https://gwar.mil.ru/gt_data/?builder=DocumentView'
        elif 'window.$.fn.initDetailBook();' in st: # type 3
            for item in soup.find_all(attrs={"data-id": True}):
                pdf_href = item['data-id']
                pdf_url = f'https://cdn.gwar.mil.ru/bookload/{pdf_href}.pdf'
                headers = {'Referer': url}
                pdf_file = os.path.join(BOOK_DIR, f'{title}.pdf')
                bro.download(pdf_url, pdf_file, headers, skip_if_file_exists=True)
            return None  # all done, no further action needed

    book_dir = ('{}_{}'.format(book_id, title))[0:224]

    ptext(f' Каталог для загрузки: {book_dir}')
    request_headers = {'referer': url}

    json_text = bro.post_text(json_url, request_headers, request_data)
    book_data = json.loads(json_text)
    pages = book_data['hits']['hits']
    for idx, page in enumerate(pages):
        if (page['_type'] == 'document_image'):
            image_url = page['_source']['path']
        elif (page['_type'] == 'stranitsa'):
            image_url = page['_source']['obraz_s_oblastyami']

        if (image_url.find('<i src="') >= 0):
            regexp = re.compile(r'<i src="(\S*?)"')
            if regexp.findall(image_url): 
                image_url = regexp.findall(image_url)[0]

        img_url = 'https://cdn.gwar.mil.ru/imagesfww/{}'.format( # либо ...ru/imageloadfull/
            image_url)
        saveImage(img_url, idx + 1, book_dir, ext, 'https://gwar.mil.ru/')
        progress(f'  Прогресс: {idx + 1} из {len(pages)} стр.')
    return title, ext


domains = {
    'elib.shpl.ru': eshplDl,
    'docs.historyrussia.org': eshplDl,
    'prlib.ru': prlDl,
    'www.prlib.ru': prlDl,
    'elibrary.unatlib.ru': unatlib_download,
    'gwar.mil.ru': gwarDL
}


def download_book(url):
    try:
        log.info(f'Скачиваю книгу {url}')
        host = urllib.parse.urlsplit(url)
        if not host.hostname:
            perror(f'Некорректный урл: {url}')
            return None
        site_downloader = domains.get(host.hostname)
        if not site_downloader:
            perror(f'Домен {host.hostname} не поддерживается')
            return None
        ptext(f'Cсылка: {url}')
        return site_downloader(url)
    except Exception as e:
        log.exception('Перехвачена ошибка в download_book')
        perror(e)
        return None


def collect_urls():
    urls = []
    if args.url:
        urls.append(args.url)
    if args.list:
        with open(args.list) as fp:
            urls.extend([line.strip() for line in fp])
    return list(
        filter(lambda x: not x.startswith('#'),
               filter(bool,
                      map(lambda x: cut_bom(x).strip(), urls))))


def main():
    try:
        global bro
        log.info('Программа стартовала')
        urls = collect_urls()
        ptext(f'Ссылок для загрузки: {len(urls)}')
        pause = 0
        if args.pause:
            pause = to_float(args.pause)
        bro = Browser(pause=pause)
        for url in urls:
            load = download_book(url)
            if load and args.pdf.lower() in ['y', 'yes']:
                progress('  Создание PDF...')
                title, img_ext = load
                img_folder_full = os.path.join(BOOK_DIR, title)
                pdf_path = os.path.join(BOOK_DIR, f'{title}.pdf')
                makePdf(pdf_path, img_folder_full, img_ext)
                ptext(f' - Файл сохранён: {pdf_path}')
    except KeyboardInterrupt:
        perror('\nЗагрузка прервана пользователем')
    except Exception as e:
        log.exception('\nПерехвачена ошибка в main')
        perror(e)
    finally:
        log.info('\nПрограмма завершена')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='booklead - Загрузчик книг из интернет-библиотек')
    parser.add_argument('--pdf', dest='pdf', default='', metavar='y', help='Создавать PDF-версии книг')
    parser.add_argument('--list', dest='list', default='', metavar='"list.txt"', help='Файл со списком книг')
    parser.add_argument('--url', dest='url', default='', metavar='"http://..."', help='Ссылка на книгу')
    parser.add_argument('--pause', dest='pause', default='0', metavar='1.0',
                        help='Пауза между HTTP-запросами в секундах')
    args = parser.parse_args()
    if args.url or args.list:
        main()
    else:
        parser.print_help()
