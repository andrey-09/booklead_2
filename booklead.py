# -*- coding: utf-8 -*-
import argparse
import json
import os
import re
import urllib.parse
import asyncio
from aiohttp import ClientSession,TCPConnector, ClientTimeout
import datetime
import time
import csv
import numpy as np
#import nest_asyncio #used for debugging
from util import CV2_Russian, number_of_images, Postprocess, Time_Processing, archive_ia, fetch_metadata, CheckArchiveForWrites
import cv2
import img2pdf
from bs4 import BeautifulSoup
import sys
from util import get_logger, headers_pr1, headers_pr2, headers_eph2
from util import md5_hex, to_float, cut_bom, perror, progress, ptext, safe_file_name, Browser, select_one_text_optional
from util import select_one_text_required, select_one_attr_required, gwar_fix_json,mkdirs_for_regular_file
from user_agent import generate_user_agent
import logging
import threading
import requests
from internetarchive import get_session
import platform #Operating system check
import subprocess #folder size for Linux

lock = threading.Lock()
lock_async = asyncio.Lock()
log = get_logger(__name__)
BOOK_DIR = 'books'

prlDl_params = {
    'ext': 'jpg' }

bro: Browser
Check_404=False
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

#---------------------------------------------------------------------- GPIB:
async def fetch_image_eshp1D1(session,url: str, headers_pr1, sem,img_path):
    """
    по url скачиваю картинку и добавляю в Файл 
    """
    flag=True
    while flag: #check, so the size is ok:
        
        async with sem:
            if STOP_break:
                return
            async with session.get(url, headers=headers_pr1) as response:
                if response.ok:
                    try: #error handling for timeout
                        with open(img_path,"wb") as file:
                            file.write(await response.read())
                        if os.path.exists(img_path):
                            if os.path.getsize(img_path)!=0:
                                flag=False
                            else:
                                await asyncio.sleep(1.2)
                        else:
                            await asyncio.sleep(1.2)
                    except Exception as Argument:
                        log.exception("Error during download:  ")
                        await asyncio.sleep(0.7)
                else:
                    log.info("Bad response from server "+str(response.status))
                    await asyncio.sleep(2)
                    if response.status==404:
                        raise AssertionError

async def async_images_eshp1D1(img_url_list,headers_eph1_list,image_path_list):
    """
    call every tile image to download in async mode и автоматически скачать книги в папку
    """#100 seamphore --too much
    sem = asyncio.Semaphore(30)##https://stackoverflow.com/questions/63347818/aiohttp-client-exceptions-clientconnectorerror-cannot-connect-to-host-stackover
    tasks=[]
    async with ClientSession(timeout=ClientTimeout(total=250, ceil_threshold=20),trust_env=True) as session: #,trust_env=True
        for i in range(len(img_url_list)):
            tasks.append(asyncio.ensure_future(fetch_image_eshp1D1(session,img_url_list[i], headers_eph1_list[i],sem,image_path_list[i])))

        await asyncio.gather(*tasks)
        
def eshplDl(url):
    ext = 'jpg'
    quality = 8
    domain = urllib.parse.urlsplit(url).netloc
    global headers_eph2
    headers_eph1=headers_eph2

    #not needed, since title is in EXCEL!
    #headers_eph1.update({'User-Agent': random.choice(user_agents)})
    #html_text = requests.get(url, headers=headers_eph1).text
    #soup = BeautifulSoup(html_text, 'html.parser')
    #title = select_one_text_optional(soup, 'title') or md5_hex(url)
    #title = safe_file_name(title)
    """
    for script in soup.find_all('script'):
    st = str(script)
    if 'initDocview' in st:
        book_json = json.loads(st[st.find('{"'): st.find(')')])
    log.info(f' Каталог для загрузки: {title}')
    pages = book_json['pages']  
    page["id"]
    """
    title=url.split("/")[-1][:40]
    
    #--------------------#get page numbers from CSV:
    database="FULL_BOOKS_GPIB.csv"
    with lock:
        with open(database,"r",encoding="utf-8-sig") as base:
            csvFile=csv.reader(base,delimiter=";")
            for row in csvFile:
                if row[2]==url:
                    pages=row[10].split(", ")
    flag=True
    while flag:  #for the case of error in main: 
        if STOP_break:
            return  
        headers_eph1_list=[]
        image_path_list=[]
        img_url_list=[]
        for idx, page in enumerate(pages):
            img_url = f'http://{domain}/pages/{page}/zooms/{quality}'
            image_short = '%05d.%s' % (idx+1, ext)
            image_path = os.path.join(BOOK_DIR, title, image_short)
            #skip, if file exists:
            mkdirs_for_regular_file(image_path)
            if os.path.isfile(image_path) and os.path.getsize(image_path)!=0:
                continue

            headers_eph1.update({'User-Agent': generate_user_agent(os='win',device_type ='desktop',navigator='chrome')})
            headers_eph1.update({'Referer': url})
            
            headers_eph1_list.append(headers_eph1)
            image_path_list.append(image_path)
            img_url_list.append(img_url)

        try:
            asyncio.run(async_images_eshp1D1(img_url_list, headers_eph1_list,image_path_list))
        except AssertionError:
                return 0
        except Exception as Argument:  #Error coding
            time.sleep(5.0)
            log.exception("Error occurred in ASYNCIO") 
        else:
            pa=os.path.join(BOOK_DIR, title)
            lst = os.listdir(pa) # your directory path
            #check on not zero:
            count_images=0
            for fi in lst:
                if os.path.getsize(os.path.join(pa,fi))!=0:
                   count_images+=1 
            if count_images==len(pages):
                flag=False
        #progress(f'  Прогресс: {idx + 1} из {len(pages)} стр.')
    return title, ext
    
#-------------------------------------------------------- PRLIB:
async def fetch_image_download(url: str, i, headers_pr1_local, session,images_folder):
    """ Не добавляйте в util.py, у меня тогда asyncio не работал (может баг на моей стороне)
    по url скачиваю картинку и добавляю в file
    """
    #proxies:https://github.com/hamzarana07/multiProxies/tree/main
    async with session.get(url, headers=headers_pr1_local) as response:
        if response.ok:  
            with open(os.path.join(images_folder,str(i)+".jpg"),"wb") as file:
                file.write(await response.read())
        else:
            log.info("Bad response from server "+str(response.status))
            if response.status==404:
                raise AssertionError
async def async_images_download(semka,connections,url,nums,headers_pr1_local,images_folder,image_path,width,height):
    """
    Async downloader
    """ 
    #for each IMAGE
    global STOP_break
    global Check_404
    sem1 = asyncio.Semaphore(connections)
    async with semka: #https://docs.aiohttp.org/en/stable/client_quickstart.html
        async with ClientSession(timeout=ClientTimeout(total=8),headers=headers_pr1_local,trust_env=True) as session:
            for i in nums: #doing it for Every url of subimages:
                
                flag=True #just keep quering the connections (Until ALL IMAGES ARE PRESENT)
                count=0 #number of iterations on each picture (get rid fo the infinite loop situation)
                while flag and count<20: #while check for a complete download:
                    if STOP_break or Check_404:
                        return
                    headers_pr1_local.update({'User-Agent': generate_user_agent(os='win',device_type ='desktop',navigator='chrome') })
                    try: #catching error here
                        count+=1
                        async with sem1: 
                            await asyncio.sleep(0.01)
                            await fetch_image_download(url.format(i), i,headers_pr1_local,session,images_folder)
                    except AssertionError:
                        log.info("404 ERRORS, skipping: " + images_folder)
                        #the error is 404 (skip this book on count):
                        if count>4:
                            with lock_async:
                                Check_404=True
                            return
                    except Exception as Argument:
                        log.info("Error occurred in local asyncio (async images) - "+ images_folder)
                        await asyncio.sleep(2)
                    else:
                        #check for image size:
                        img=os.path.join(images_folder, str(i)+".jpg")
                        if os.path.exists(img):
                            if os.path.getsize(img)!=0:
                                flag=False
    #Double check on the number of items:
    lst=os.listdir(images_folder)
    if len(lst)==width*height:
        #after download of all images create the BIG ONE:
        if not await Postprocess(images_folder,width,height, image_path):
            log.info("Processing image error - " + images_folder)
async def PresLib_Main_Download(pages,book, title,url):
    """
    Супер быстрый загрузчик Президентской библиотеки
    Main function, where each url is created and it's later on passed to function to download each page
    """
    #num_of_pages_down=1 #for the time prediction
    #start=datetime.datetime.now()#for the time prediction
    # and pass the result for DOWNLOAD
    #ON ERROR CREATE THE DATA FOR DOWNLOAD::
    check=True #repeat 1-3 time to gather all the images
    count_loop=0
    while check:
        data={}

        counter=0 #check the pages
        global headers_pr1
        headers_pr1_local=headers_pr1
        while counter<len(pages): # CREATE the DATA for Download + create FOLDER strcuture
            idx=counter
            page=pages[counter]
            #force downloading every page

            img_url = 'https://content.prlib.ru/fcgi-bin/iipsrv.fcgi?FIF={}/{}&JTL={},'.format(
                book['imageDir'], page['f'], page['m']) #поменял здесь немного вид урл, так как по частям качаю
            # брал урл отсюда: https://iipimage.sourceforge.io/documentation/protocol
            img_url+="{}"
            width, height=number_of_images(page["d"][len(page['d']) - 1]['w'],page["d"][len(page['d']) - 1]['h']) 
            image_short = '%05d.%s' % (idx+1, "jpg")
            image_path = os.path.join(BOOK_DIR, title, image_short)
            headers_pr1_local.update({'Referer': url})
            #created the DATA
            #check for what was ALREADY DOWNLOADED
            if os.path.exists(image_path) and os.stat(image_path).st_size > 0:
                log.info(f'Пропускаю скачанный файл: {image_path}')
                counter+=1
                #progress(f'  Прогресс: {idx + 1} из {len(pages)} стр. ')
            else: 
                #mkdirs_for_regular_file(image_path)
                
                images_folder=os.path.join(BOOK_DIR, title,"images"+str(counter))
                nums=range(width*height)  
                try:
                    os.makedirs(images_folder)
                except FileExistsError:
                    pass  
                good_nums=[] #check what subimages for each image are present
                for num in nums:
                    if not (os.path.isfile(os.path.join(images_folder,str(num)+".jpg")) and os.path.getsize(os.path.join(images_folder,str(num)+".jpg"))!=0):
                        good_nums.append(num)
                nums=good_nums   
                counter+=1
                data[idx]=[img_url,image_path,images_folder,headers_pr1_local,nums,width, height] 
        
        #DOWNLOAD the LEFT images: 
        try:
            #create All coroutines to Run:
            global Cores #Total amount of connections: number_of_images_huge*nums*Cores
            Total_number=200 #per core
            #speed 10 images/minute-> 10 images*200subs-> 2000subimages perminnute-> 1 subimmage -5secs ->
            connections=10 #amount of connections to subimages in a folder:
            folder_connections=Total_number//connections
            #connections=max(Total_number//(Cores*len(data)),3)
            semka = asyncio.Semaphore(folder_connections)
            #sem1 = asyncio.Semaphore(10)
            #https://pawelmhm.github.io/asyncio/python/aiohttp/2016/04/22/asyncio-aiohttp.html
            coroutines=[]
            for key, value in data.items(): #iterateing over ALL IMAGES gathered:
                coroutines.append(async_images_download(semka,connections,value[0],value[4],value[3],value[2],value[1],value[5],value[6]))
            #limit amount of folder executed at the same time:
            await asyncio.gather(*coroutines)
        except Exception as Argument:  #Error coding
            time.sleep(2.)
            log.exception("Error occurred in the folder "+title)  
        else:
            director=os.path.join(BOOK_DIR, title)
            lst=os.listdir(director)
            count_images=0
            for f in lst:
                if f.endswith(".jpg"):
                    count_images+=1
            if count_images==len(pages):
                check=False
            
        if count_loop>3: #only repeat itself max.4 times
            check=False
        count_loop+=1

def prlDl(url):
    """
    Президентская библиотека имени Б.Н. Ельцина
    Формат - серия изображений
    Пример урла книги (HTML) - https://www.prlib.ru/item/420931
    """
    ext = prlDl_params['ext']
    global headers_pr2
    html_text = requests.get(url, headers=headers_pr2).text
    soup = BeautifulSoup(html_text, 'html.parser')
    # instead of Title use unique identitfier of the url
    title_name = soup.head.title.text.split("|")[0]
    title_name = safe_file_name(title_name)
    #get the number of characters in the current path
    num_of_characters=150-len(os.path.abspath(os.getcwd()))
    if len(title_name)>165:
        title_name=title_name[:num_of_characters] + title_name[-15:]#to have the volume part in the name
    
    title=url.split("/")[-1]
    
    log.info(f'Каталог для загрузки: {title_name}')
    
    for script in soup.find_all('script'): #findAll deprecated
        st = str(script)
        if 'jQuery.extend' in st:
            book_json = json.loads(st[st.find('{"'): st.find(');')])
            
            try:
                if "item" in url.split("prlib.ru/")[1]:   #case for https://www.prlib.ru/item/*** 
                    book = book_json['diva']['1']['options']
                elif "node" in url.split("prlib.ru/")[1]:     #case for https://www.prlib.ru/node/***
                    book = book_json['diva']['settings']
            except:
                log.exception("Error, NOTHING FOUND!")
                return
    json_text = bro.get_text(book['objectData'],headers=headers_pr2)
    book_data = json.loads(json_text)
    pages = book_data['pgs']
    # run asyncio:
    #nest_asyncio.apply()
    asyncio.run(PresLib_Main_Download(pages, book, title,url))
    #check for the number of images downloaded:
    director=os.path.join(BOOK_DIR, title)
    lst=os.listdir(director)
    count_images=0
    for f in lst:
        if f.endswith(".jpg"):
            count_images+=1
    if count_images==len(pages):
        return title_name, ext
    else:
        return 0

#------------------------------------------------
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
#-----------------------------------------------------

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
        log.info(f'Cсылка: {url}')
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
        with open(args.list,"r", encoding="utf-8") as fp:
            urls.extend([line.strip() for line in fp])
    return list(
        filter(lambda x: not x.startswith('#'),
               filter(bool,
                      map(lambda x: cut_bom(x).strip(), urls))))
def worker(file_urls,i):
    

    with open(file_urls, 'r') as f:
        numberoflines = len(f.readlines())
    global STOP_break
    
    for j in range(numberoflines):
        file=open(file_urls,"r+")
        urls=file.read().splitlines()
        url=urls[0]
        if STOP_break:
            file.close()
            break
        
        if args.archive: #do NOT download duplicates
            #search, whether it was already downloaded
            with lock:
            #if source_urls doesn't exist/too old (2 hours old): make it:
                if not os.path.isfile("source_urls.txt") or (time.time()-os.path.getmtime("source_urls.txt"))>3600:
                    #modify source_urls
                    
                    with open("personal_data.txt","r") as file2:
                        session=file2.read().splitlines()
                    
                    c = {'s3': {'access': session[0], 'secret': session[1]}}
                    s = get_session(config=c)
                    check_flag=True
                    while check_flag:
                        try:
                            query='uploader:"pavelserebrjanyi@gmail.com" AND mediatype:texts AND source_url:*elib.shpl.ru*'
                            items=s.search_items(query, fields=["source_url"], max_retries =100,request_kwargs={'timeout':(300,300)},params={"page":1,"rows":30000})
                            # issue with readTimeout is solved by using advanced_search: add params={'page':1, 'rows':70000}
                            #https://github.com/jjjake/internetarchive/issues/610
                            source_urls=[]
                            for item in items:
                                if "source_url" in item.keys():
                                    source_urls.append(item["source_url"])
                        except:
                            log.exception("Problems with IA servers")
                            time.sleep(2)
                            #servers are overloaded
                            #with lock:
                            #    args.archive=0
                        else:
                            check_flag=False
                            with open("source_urls.txt","w") as file3:
                                file3.write("\n".join(source_urls))
            
            with open("source_urls.txt","r") as file1:
                source_url=file1.read().splitlines()
            if url in source_url:
                #delete the first LINE from the NOTEPAD
                file.seek(0)
                # truncate the file
                file.truncate()
                # start writing lines except the first line
                if len(urls)==1:
                    break
                file.write('\n'.join(urls[1:]))
                file.close()
                continue

        load = download_book(url)
        if STOP_break:
            file.close()
            break
        try:
            if not isinstance(load, tuple):
                raise Exception("Not able to download!")
        except:
            log.exception("NO download!")
            file.seek(0)
            # truncate the file
            file.truncate()
            # start writing lines except the first line
            if len(urls)!=1:
                file.write('\n'.join(urls[1:]))
                file.write('\n'+urls[0])
            file.close()
            continue
        else:
            if not args.archive:
                #delete the first LINE from the NOTEPAD
                file.seek(0)
                # truncate the file
                file.truncate()
                # start writing lines except the first line
                if len(urls)!=1:        
                    file.write('\n'.join(urls[1:]))
                file.close()
        log.info(f'Thread {i} finished downloading')
        if args.archive and not STOP_break:
            #archive all photos:
            try:
                #fetch metadata:
                domain = urllib.parse.urlsplit(url).netloc
                metadata=fetch_metadata(url,domain)
                archive_ia(load[0],url,metadata) #archive the book
            except:
                #if an error, skip to the next one
                if len(urls)!=1:
                    file.seek(0)
                    # truncate the file
                    file.truncate()
                    # start writing lines except the first line
                    file.write('\n'.join(urls[1:]))
                    file.write('\n'+urls[0])
                file.close()
                continue
            else:
                #delete the first LINE from the NOTEPAD
                file.seek(0)
                # truncate the file
                file.truncate()
                # start writing lines except the first line
                if len(urls)!=1:
                    file.write('\n'.join(urls[1:]))
                    #file.write('\n'+urls[0])
                file.close()
            log.info(f'Thread {i} archived the book')
        #NOT USED (with archive will not work, since i delete the folder)
        if load and args.pdf.lower() in ['y', 'yes'] and not STOP_break:
            progress('  Создание PDF...')
            title_name, img_ext = load
            title=url.split("/")[-1]
            img_folder_full = os.path.join(BOOK_DIR, title)
            pdf_path = os.path.join(BOOK_DIR, f'{title_name}.pdf')
            makePdf(pdf_path, img_folder_full, img_ext)
            ptext(f' - Файл сохранён: {pdf_path}')
        log.info(f'Thread {i} is DONE with the book')
        if STOP_break:
            file.close()
            break

    log.info(f'Thread {i} is FINISHED!')
            

def main():
    try:
        global bro
        if args.archive and not os.path.exists("personal_data.txt"): #personal infroamtion for archive.org
            sys.stdout.write("Вы хотите закачать на сервер archive.org Нужны входные данные\n")
            access_key=input("Your S3 access key: ")
            secret_key=input("Your S3 secret key: ")
            with open("personal_data.txt", "w") as file:
                file.write(access_key+"\n"+secret_key)
        

        log.info('Программа стартовала')
        urls = collect_urls()
        
        ptext(f'Ссылок для загрузки: {len(urls)}')
        pause = 0
        if args.pause:
            pause = to_float(args.pause)
        bro = Browser(pause=pause)
        
        
        #divide urls in Cores and Run:
        global Cores
        Cores=args.cores
        #create Threds:
        threads=[]
        #create urls:
        koef=len(urls)//Cores
        global STOP_break
        STOP_break=False # for stoppage
        
        #create new urls in files:
        if not args.continue1:
     
            for i in range(Cores):
                if i==Cores-1:
                    with open(f"urls_{i}.txt", "w") as file:
                        file.write('\n'.join(urls[koef*i:]))
                else:
                    with open(f"urls_{i}.txt", "w") as file:
                        file.write('\n'.join(urls[koef*i:koef*(i+1)]))
                       
        for i in range(Cores):
            threads.append(threading.Thread(target=worker, args=(f"urls_{i}.txt",i,)))
            
        for i in range(Cores):
            threads[i].start()
            log.info(f'Thread {i} is starting')
        #Operating system check:
        plat=platform.system()
        try:
            timer=0
            while any([ threads[i].is_alive() for i in range(Cores)]):
                time.sleep(20)

                timer+=1
                if timer==360: #check size every 2 hours
                    if plat=="Windows": #windows foldsize:
                        #check for the size:
                        import win32com.client as com #for windows folder size (if imported not here, error on Linux)
                        fso = com.Dispatch("Scripting.FileSystemObject")
                        folder = fso.GetFolder(BOOK_DIR)
                        size=folder.Size/2**30 #GB
                    else: #both "Linux" and Mac
                        res=subprocess.run(['du', '-sb',BOOK_DIR], capture_output=True, text=True)
                        size=int(res.stdout.split()[0])/2**30 #GB
                        
                    if size>args.max_size:
                        print(f"Folder size is larger than {args.max_size} GB -> Stopping the Script")
                        STOP_break=True
                        break
                    timer=0
                
                #check for the submitted url to be on archive.org (if archive selected and mark it in excel)
                #if args.archive:
                #    CheckArchiveForWrites(urls)
            
        except KeyboardInterrupt:
            perror(' Загрузка прервана пользователем')
         
            STOP_break=True
        #CheckArchiveForWrites(urls)  
        for i in range(Cores): #it waits for everything to finish
            threads[i].join()
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
    parser.add_argument('--cores', dest='cores',default='1', metavar='1', help='На скольких корах ранить',type=int)
    parser.add_argument('--continue', dest='continue1',default='0', metavar='0', help='Продолжить ли прошлое прерванное скачивание (ссылки в "urls_.txt")? (0/1)',type=int)
    parser.add_argument('--archive', dest='archive',default='0', metavar='0', help='(0/1) Загрузить ли книгу в Онлайн Архив archive.org (для удобной конвертации и оптимизации)',type=int)
    parser.add_argument('--max_size', dest='max_size',default='100', metavar='100', help='Максимальный размер папки с загрузками в ГБ',type=float)
    args = parser.parse_args()
    if args.url or args.list:
        main()
    else:
        parser.print_help()