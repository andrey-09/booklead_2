from internetarchive import get_session
import os
directory="..\\SENT_TO_DOWNLOAD"

c = {'s3': {'access': 'qJaX9KKXhXkzoN5o', 'secret': 'mmI4XUkxM9O8gZ15'}}
s = get_session(config=c)
query='uploader:"pavelserebrjanyi@gmail.com" AND mediatype:texts'
items=s.search_items(query, fields=["source_url"], params={'page':1, 'rows':70000})
source_urls=[]
for item in items:
    source_urls.append(item["source_url"])

#go trhough each file and update it:

for subdir, dirs, files in os.walk(directory):
    for file in files:
        filepath = subdir + os.sep + file
        with open(filepath,"r") as f1:
            urls=f1.read().splitlines()
        not_yet=[]
        for url in urls:
            if url not in source_urls:
                not_yet.append(url)
        with open(filepath,"w") as f1:
            f1.write("\n".join(not_yet))