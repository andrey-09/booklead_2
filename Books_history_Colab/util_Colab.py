# -*- coding: utf-8 -*-
import codecs
import datetime
import errno
import functools
import hashlib
import logging
from logging.handlers import RotatingFileHandler                                     
import numpy as np
import os
import random
import re
import shutil
import sys
import time
import cv2
import requests
import threading
from bs4 import Tag
from requests import Response
from typing import Dict, Optional, Pattern, Union
import json
from random import randrange
import csv
import transliterate 
import internetarchive
from internetarchive.session import ArchiveSession
from user_agent import generate_user_agent                                          
from internetarchive import search_items
from langdetect import detect #language detection
user_agents = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',
    'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0'
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
]
lock=threading.Lock()
Google_Drive_Path="drive/MyDrive/Books_download/"
LOG_FILE = 'log.txt'
logging_set_up = False


def _setup_logging():
    time_format = '%Y-%m-%d %H:%M:%S'
    log_formatter = logging.Formatter("%(asctime)s %(levelname)-5.5s %(message)s", time_format)
    log_level = os.getenv('LOGLEVEL', 'INFO')
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    if root_logger.hasHandlers():
        # https://stackoverflow.com/questions/7173033/duplicate-log-output-when-using-python-logging-module
        root_logger.handlers.clear()

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=20*1024*1024,backupCount=2, encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
    logging.basicConfig(filemode='w') 
    if os.getenv('LOGTOCONSOLE', '0') == '1':
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)


def get_logger(name=None):
    if not logging_set_up:
        _setup_logging()
    return logging.getLogger(name)


log = get_logger(__name__)
lock=threading.Lock()




def perror(msg):
    """печать ошибки на экран, не может быть стёрто"""
    log.error(f'Ошибка отображена пользователю: {msg}')
    sys.stdout.write(f'\rОшибка: {msg}\n')


def ptext(msg):
    """печать обычного сообщения на экран, не может быть стёрто"""
    log.info(f'Сообщение отображено пользователю: {msg}')
    sys.stdout.write(f'\r{msg}\n')


def progress(msg):
    """печать строки прогресса, стирает текущую строку"""
    sys.stdout.write(f'\r{msg}')


def mkdirs_for_regular_file(filename: str):
    """Создаёт все необходимые директории чтобы можно было записать указанный файл"""
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
        except OSError as e:  # Guard against race condition
            if e.errno != errno.EEXIST:
                raise
def Time_Processing(timedelta):
    """Чтоб время показывать
    """
    minutes, seconds = divmod(round(timedelta.total_seconds()), 60)
    return minutes, seconds
def fetch_metadata(url,headers_pr2):
        #fetch metadata:
    from bs4 import BeautifulSoup
    import requests

    html_text =requests.get(url,headers=headers_pr2).text
    soup = BeautifulSoup(html_text, 'html.parser')
    if url.split("https://")[1][4:9]=="prlib": #prlib.ru metadata
        title = soup.head.title.text.split("|")[0]
        full_title=title
        if len(title)>210:
            end_on_space=" ".join(title[:210].split(" ")[:-1])
            title=end_on_space+" ..."
        authors=soup.find("ul",{"class":"field field-name-field-book-author field-type-taxonomy-term-reference field-label-hidden"})
        author_=[]
        try:
            for author in authors.find_all("a"):
                author_.append(author.text)
        except:
            author_=""
            
        description=""
        td_check=soup.find("div",{"class":"field field-name-field-book-bd field-type-text-long field-label-hidden"}).find_all("td")
        if len(td_check)!=0: #check for zero td
            for desc in td_check[1:][:-1]:
                if desc.td is None and desc.get_text(strip=True)!="":
                    description+=desc.get_text(strip=True).replace("\n","")+"\n"
        
        #collection+catalog form a subject:
        #Catalogs
        subjects=[]
        catalogs=soup.find_all(class_="df-bbk")
        if len(catalogs)!=0:
            for subject in catalogs[0].find_all("li"):
                subjects.append(subject.text.strip())
        
        #Collections: #ADD THEM to DESCRIPTION
        subject_set=[]
        collections=soup.find_all(class_="df-relations")
        if len(collections)!=0:
            for subject in collections[0].find_all("li"):
                description+=subject.text+"\n"
                for element in subject.text.split(" → ")[:-2]:
                    subject_set.append(element)
        subjects=subjects+list(dict.fromkeys(subject_set))
        #description+="\n"+url+"\n"
        #language detection:
        lang=detect(title)
        dict_lang={"de":"German", "en":"English"}
        if lang in list(dict_lang.keys()):
            language=dict_lang[lang]
        else:
            language="Russian"
        
        #add "date" after the data is scrapped
        #search by date in .csv?
        global Google_Drive_Path
        dataset=Google_Drive_Path+"PrLib_Dataset.csv"
        #adding date
        date=""
        if os.path.exists(dataset):
            with lock:  
                with open(dataset, mode ='r',encoding="utf-8")as file:
                  csvFile = csv.reader(file)
                  for lines in csvFile:
                        if url==lines[2]:
                            date=lines[0]
    return {
        "collection":["russian-online-libraries"],
        "creator" : author_,
        "language" : language,
        "mediatype" : "texts",
        "Full_title": full_title,
        "title" : title,
        "description":   description,
        "subject":subjects,
        "date":date,
        "Source_url": url
        #"script_down":"Colab"
        }
def archive_ia(title, url, metadata):
    """
    Function to upload the downloaded book to archvie.org, with all the metadata needed
    """
    global Google_Drive_Path
    #secret data:
    with lock:          
        with open(Google_Drive_Path+"personal_data.txt","r") as file:
            session=file.read().splitlines()
        
    
    #make preparations llike renameing, moving, zipping:
    new_title=transliterate.translit(title, "ru",reversed=True).replace(" ","")[:40]+str(randrange(99))
    new_title = re.sub(r'[^a-zA-Z0-9_]', '', new_title) #remove all special characters
    new_title=new_title.lower()
    title_file=url.split("/")[-1]
    #check, whether a file is already there (because it was already tried before)
    #import glob
    #if glob.glob('books\\'+new_title[:-2]+'*.zip'):
    os.rename("books/"+title_file, "books/"+new_title)
    root="books/"+new_title
    for dir, subdirs, files in os.walk(root):
        for f in files:
            f_new = new_title+ f
            os.rename(os.path.join(root, f), os.path.join(root, f_new))

    shutil.make_archive(root,'zip',"books",new_title)
    new_name=root+"_images.zip"
    os.rename(root+".zip", new_name) #https://help.archive.org/help/how-to-upload-scanned-images-to-make-a-book/
    
    #creating data and transferring Data to Server:
    try:
        response=internetarchive.upload(new_title, new_name, metadata, verify=True,validate_identifier=True,verbose=True,retries=20, retries_sleep =3, queue_derive=True,access_key=session[0], secret_key=session[1])
        if not response[0].ok:
            raise Exception("Not UPLOADED! Status Code ERROR!")
    except Exception as Argument:
        logging.exception("Error occurred in Ineren archvie upload "+response[0].reason) 
    
        os.rename("books/"+new_title,"books/"+title) #rename folder
        os.remove(new_name) #delete zip
        #rename the files back:
        root="books/"+title
        shutil.rmtree(root)
        raise Exception("Error wiht UPLOAD")
        
    else:
        #os.rename("books/"+new_title,"books/"+title) #rename folder
        os.remove(new_name) #delete zip
        #rename the files back:
        root="books/"+new_title                     
        shutil.rmtree(root)
  
    
def CheckArchiveForWrites(urls):
    """DROPPED!
    Function to check, whether a book is written to archive.org and update Excel (for keeping track of records)
    takes a lot of time and unneccesary
    """
    all_titles=[]
    datafile="Prlib_1801-1900.csv"
    with open(datafile, mode ='r',encoding="utf-8")as file:
        csvFile = csv.reader(file)
        for lines in csvFile:
            for url in urls:
                if url==lines[2] and lines[3]!="1": 
                    
                    all_titles.append(lines[1]) #write all titles to search for
    
    s = ArchiveSession()
    today=datetime.datetime.today().strftime('%Y-%m-%d')
    search = s.search_items('uploader:"pavelserebrjanyi@gmail.com" AND addeddate:'+today, fields=["title"])
    for title in all_titles:
        for result in search:
            if result["title"] in title: #so, there is a common thing; change the csv value:
                
                with open(datafile,"r", encoding='utf-8') as csvfile: #read the place, where to put value
                    f = csv.reader(csvfile)
                    data=list(f)
                    title_column=[i[1] for i in data]
                    ind=title_column.index(title)
                    data[ind][3]=1
                    
                with open(datafile, 'w', newline='', encoding='utf-8') as file: #put the value
                    writer = csv.writer(file)
                    writer.writerows(data)

async def Postprocess(images_folder,width, height,image_path):
    """
     Прохожу через бинарные данные в results_prlDl, ставлю их на правильные места в картинке исходной и вывожу все в файл, напртмер 0001.jpg
    """
    Total_Image=[i for i in range(width*height)]
    #iterate through each file and add them:
    for item in range(width*height):
        #read from file:
        Total_Image[item]=CV2_Russian(os.path.join(images_folder, str(item)+".jpg")) # название папки на Русском в названии мешало прочитать cv2 файл (это окалаось известный баг cv2)
    #delete images folder:
    shutil.rmtree(images_folder)
    regroup=[]
    for h in range(height):
        regroup.append(Total_Image[h*width:(h+1)*width])
    try:
        im_h=cv2.vconcat([cv2.hconcat(item) for item in regroup])

    #cv2.imwrite(image_path, im_h) (doesn't work with Russian)
        result, data = cv2.imencode('.jpg', im_h)
    except:
        return False
    fh = open(image_path, 'wb')
    fh.write(data)
    fh.close()
    return True
def number_of_images(width, height):
    """
    получаю кол-во картинок по ширине и длине (возможно можно в одну строчку как-то:)
    """
    num_w=width//256
    if width%256!=0:
        num_w+=1
    num_h=height//256
    if height%256!=0:
        num_h+=1
    return int(num_w),int(num_h)  

def CV2_Russian(name):
    """
    Чтение картинки с русским названием в пути в cv2
    #https://answers.opencv.org/question/205345/imread-and-russian-language-path-to-img/
    """
    f = open(name, "rb")
    chunk = f.read()
    chunk_arr = np.frombuffer(chunk, dtype=np.uint8)
    img = cv2.imdecode(chunk_arr, cv2.IMREAD_COLOR)
    f.close()         
    return img
    
    
def cut_bom(s: str):
    bom = codecs.BOM_UTF8.decode("utf-8")
    return s[len(bom):] if s.startswith(bom) else s


def to_float(s: str, fallback=0.0):
    try:
        return float(s)
    except ValueError:
        return fallback


def md5_hex(s: str) -> str:
    md5 = hashlib.md5()
    md5.update(s.encode('utf-8'))
    return md5.hexdigest()


def gwar_fix_json(s: str, a: bool = False) -> str:
    s = ' '.join(s.split())
    s = s.replace('"', "\'")
    s = s.replace("'", '"')
    if a:
        # https://stackoverflow.com/questions/50947760/how-to-fix-json-key-values-without-double-quotes
        s = re.sub(r"(\w+):", r'"\1":', s) #added r: https://stackoverflow.com/questions/50504500/deprecationwarning-invalid-escape-sequence-what-to-use-instead-of-d 
    json_s = json.loads(s)
    return json_s


def random_pause(target_pause: float):
    return random.uniform(
        target_pause - target_pause * 0.5,
        target_pause + target_pause * 0.5)


def select_one_required(root: Tag, selector: str) -> Tag:
    tag = root.select_one(selector)
    if not tag:
        raise Exception(f'Не найден элемент по пути {selector}')
    return tag


def select_one_text_required(root: Tag, selector: str):
    tag = root.select_one(selector)
    if not tag:
        raise Exception(f'Не найден элемент по пути {selector}')
    text = tag.text.strip()
    if not text:
        raise Exception(f'Не найден text у элемента по пути {selector}')
    return text


def select_one_text_optional(root: Tag, selector: str):
    tag = root.select_one(selector)
    if not tag:
        raise Exception(f'Не найден элемент по пути {selector}')
    text = tag.text if tag else ''
    return text.strip()


def select_one_attr_required(root: Tag, selector: str, attr_name: str):
    tag = root.select_one(selector)
    if not tag:
        raise Exception(f'Не найден элемент по пути {selector}')
    val: str = tag.get(attr_name)
    val = val.strip() if val else val
    if not val:
        raise Exception(f'Не найден аттрибут {attr_name} у элемента по пути {selector}')
    return val


def safe_file_name(value: str):
    if not value:
        return value
    value = re.sub(r'[^\w\s()\[\]{}.,-]+', ' ', value, flags=re.UNICODE)
    value = re.sub(r'[\s]+', ' ', value)
    value = value.strip(' \t.,')  # точка на конце запрещена в Windows
    return value


last_time_connected: Optional[datetime.datetime] = None


def pausable(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global last_time_connected
        bro: Browser = args[0]
        if last_time_connected and bro.pause:
            pause = random_pause(bro.pause) - (datetime.datetime.now() - last_time_connected).total_seconds()
        else:
            pause = 0
        if pause > 0:
            log.info(f'Сплю %.3f сек' % pause)
            time.sleep(pause)
        last_time_connected = datetime.datetime.now()
        return func(*args, **kwargs)
    return wrapper


class Browser:

    def __init__(self, pause: float):
        self.pause = pause

    @pausable
    def get_text(self, url: str, headers: Dict = None, content_type: str = None):
        headers = self._prepare_headers(headers)
        log.info(f'Запрашиваю GET {url}')
        log.info(f'Заголовки: {headers}')
        response = requests.get(url, headers=headers)
        log.info(f'Ответ: {response.status_code} {response.reason}')
        log.info(f'Заголовки: {response.headers}')
        self._validate_response(response, url, content_type)
        return response.text

    @pausable
    def post_text(self, url: str, headers: Dict = None, data: Dict = None, content_type: str = None):
        headers = self._prepare_headers(headers)
        log.info(f'Запрашиваю POST {url}')
        log.info(f'Заголовки: {headers}')
        response = requests.post(url, headers=headers, data=json.dumps(data))
        log.info(f'Ответ: {response.status_code} {response.reason}')
        log.info(f'Заголовки: {response.headers}')
        self._validate_response(response, url, content_type)
        return response.text

    @pausable
    def download(self, url: str,
                 fpath: str,
                 headers: Dict = None,
                 content_type: Union[str, Pattern] = None,
                 skip_if_file_exists=False):
        global last_time_connected
        progress(f' - Скачиваю {url}')
        if skip_if_file_exists and os.path.exists(fpath) and os.stat(fpath).st_size > 0:
            log.info(f'Пропускаю скачанный файл: {fpath}')
            last_time_connected = None
            return
        headers = self._prepare_headers(headers)
        log.info(f'Запрашиваю GET {url}')
        log.info(f'Заголовки: {headers}')
        response = requests.get(url, stream=True, headers=headers)
        log.info(f'Ответ: {response.status_code} {response.reason}')
        log.info(f'Заголовки: {response.headers}')
        self._validate_response(response, url, content_type)
        mkdirs_for_regular_file(fpath)
        with open(fpath, 'wb') as fd:
            shutil.copyfileobj(response.raw, fd)
        length = os.stat(fpath).st_size
        ptext(f' - Сохранено в файл {fpath} ({length} байт)')

    def _prepare_headers(self, additional_headers: Dict):
        headers = additional_headers if additional_headers else {}
        headers.update({'User-Agent': generate_user_agent(os='win',device_type ='desktop',navigator='chrome')})
        return headers

    def _validate_response(self, response: Response, url, expected_ct: Union[str, Pattern]):
        if not response.ok:
            raise Exception(f'Не удалось скачать файл {url} - {response.status_code} {response.reason}')
        if expected_ct:
            actual_ct: str = response.headers.get('content-type')
            if actual_ct:
                if isinstance(expected_ct, Pattern):
                    if not expected_ct.match(actual_ct):
                        perror(f'Некорректный content-type {actual_ct} по адресу {url}')
                else:
                    if actual_ct != expected_ct:
                        perror(f'Некорректный content-type {actual_ct} по адресу {url}')


if __name__ == '__main__':
    print(safe_file_name("  Привет  -.—.–  Москва 1989 XVII () {} [] ,. Hello ?!|/\\ - ӘәӨөҮү  "))
