#process books fromm txt's:
#Scrapped data:
scrapped="result_data_pages_intermediary.txt"
txt_first='pages_to_find.txt'
check_new_db="Prlib_test_pages.csv"
to_add_to= "Prlib_1921-2000.csv"
   
   #https://www.prlib.ru/item/460792 
   #https://www.prlib.ru/item/426868
import csv

with open(scrapped, "r") as file:
    data=file.read().splitlines()


with open(txt_first, 'r', newline='',encoding="utf-8") as fileurls:
    urls=fileurls.read().splitlines()

urls=[[url] for url in urls]
urls=[["links","pages"]] + urls
#add a data_page column
#data_file[0].append("pages")


for dat in data:
    ind=int(dat.split(",")[0])
    numb_pages=dat.split(",")[1]
    urls[ind+1].append(numb_pages)
   
with open(check_new_db, 'w', newline='', encoding='utf-8') as file: #put the value
    writer = csv.writer(file)
    writer.writerows(urls)


 # ONLY FOR WRITING in the Overview Database
with open(to_add_to, 'r', newline='',encoding="windows-1251") as csvfile:
    f = csv.reader(csvfile)
    data_file=list(f)
"""
links=[]
for url in data_file:
    links.append(url[2])
for url,pages in urls[1:]:
    ind=links.index(url)
    data_file[ind][3]=pages
with open(to_add_to, 'w', newline='', encoding='windows-1251') as file: #put the value
    writer = csv.writer(file)
    writer.writerows(data_file)
"""
