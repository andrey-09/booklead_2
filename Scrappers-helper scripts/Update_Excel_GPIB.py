import csv
import time
start=time.time()
#update Excel:
# set everything to 0:
from internetarchive import get_session
c = {'s3': {'access': 'qJaX9KKXhXkzoN5o', 'secret': 'mmI4XUkxM9O8gZ15'}}
s = get_session(config=c)
query='uploader:"pavelserebrjanyi@gmail.com" AND mediatype:texts AND source_url:*elib.shpl.ru*'
items=s.search_items(query, fields=["source_url"])
source_urls=[]
for item in items:
    source_urls.append(item["source_url"])

datafile="..\\databases\\FULL_BOOKS_GPIB_DONE.csv"
with open(datafile,"r", encoding='utf-8-sig') as csvfile: #read the place, where to put value
    f = csv.reader(csvfile,delimiter=";")
    data=list(f)
"""
with open(datafile[:-4]+"_BACKUP.csv", 'w', newline='', encoding='windows-1251') as file: #put the value
    writer = csv.writer(file)
    writer.writerows(data)
"""
for url in source_urls:
    url_column=[i[2] for i in data]
    try:
        ind=url_column.index(url)
        data[ind][11]=1
    except:
        print("NOT FOUND: - ", url)
        continue
                        
with open(datafile, 'w', newline='', encoding='utf-8-sig') as file: #put the value
    writer = csv.writer(file,delimiter=";")
    writer.writerows(data)

print("Time taken: ", time.time()-start)