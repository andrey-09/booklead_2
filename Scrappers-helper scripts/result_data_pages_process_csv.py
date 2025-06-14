#process books:
#Scrapped data:
scrapped="result_data_pages_intermediary.txt"
database='Prlib_1901-1920.csv'
new_db="Prlib_1901-1920_pages.csv"
    
    
import csv
with open(scrapped, "r") as file:
    data=file.read().splitlines()


with open(database, 'r', newline='',encoding="utf-8") as csvfile:
    f = csv.reader(csvfile)
    data_file=list(f)

#add a data_page column
data_file[0].append("pages")


for dat in data:
    ind=int(dat.split(",")[0])
    numb_pages=dat.split(",")[1]
    data_file[ind+1].append(numb_pages)
    
with open(new_db, 'w', newline='', encoding='utf-8') as file: #put the value
    writer = csv.writer(file)
    writer.writerows(data_file)