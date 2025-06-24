from selenium_driverless.types.by import By
from selenium_driverless import webdriver
import asyncio
import csv
all_urls=[]
"""
with open('Prlib_1901-1920.csv', 'r', newline='',encoding="utf-8") as csvfile:
    writer = csv.DictReader(csvfile)
    for row in writer:
        all_urls.append(row["link"])
"""
with open("pages_to_find.txt","r") as file1:
    all_urls=file1.read().splitlines()        

import logging
async def scrape_data_async(url, ind,driver,sem):
    retry=0
    total_retries=2
    while retry<total_retries:
        async with sem:
            try:
                
                driver1 = await driver.new_window("tab", activate=False)
                await driver1.get(url)
                #check on №
                title=await driver1.find_element(By.CLASS_NAME, 'page-title', timeout=20)
                title=await title.text
                if "№" in title:
                    await driver1.close()
                    print(ind)
                    return (ind,"")  #Тольские ведомости и все газетыы
                    
                element = await driver1.find_element(By.ID, 'diva-1-num-pages', timeout=20)
                pages=await element.text
                await driver1.close()
            except:
                await driver1.close()
                time.sleep(1)
                #logging.exception("Error")
                if retry==total_retries-1:
                    data_entry=(ind,"")
                retry+=1
            else:
                data_entry=(ind,pages)
                retry=total_retries

            
    print(ind)
    return data_entry
def write_to_file(resu):
    with open("result_data_pages_intermediary.txt","a") as file:
        count=0
        for item in resu:
            if item=="":
                file.write(str(-1))
            else:
                file.write(str(int(item)))
            if count==0:
                file.write(",")
            else:
                file.write("\n")
            count+=1


import time
start1=time.time()

# list to store the threads
threadList = []

#https://github.com/kaliiiiiiiiii/Selenium-Driverless - TOP
#for each url:
#create Indeces to download

Indeces=[]
with open("result_data_pages_intermediary.txt","r") as file12:
    data=file12.read().splitlines()
    indec=[int(i.split(",")[0]) for i in data]
    for ind in range(len(all_urls)):
        if ind not in indec:
            Indeces.append(ind)
   
#sort the indeces + find which ones are missing from all_urls -those to download
#print(Indeces[:50])
# implement to start automatically!
#import sys
#sys.exit()

lock = asyncio.Lock()
async def main():
    sem=asyncio.Semaphore(3)
    options = webdriver.ChromeOptions()
    options.headless=False
    
    async with webdriver.Chrome(options=options) as driver:
        threads=[]
        for ind in Indeces:
            threads.append(scrape_data_async(all_urls[ind],ind,driver,sem))
           
        for coro in asyncio.as_completed(threads):
            result=await coro
            #saving index:
            async with lock:
                write_to_file(result)
#https://github.com/encode/uvicorn/discussions/2105
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#import nest_asyncio
#nest_asyncio.apply()
asyncio.run(main())            

print(time.time()-start1)

#with open("result_data_pages.txt", "w") as file:
#    file.write("\n".join(result))