import os
urls=[]
for f in os.listdir():
    if "urls_" in f:
       with open(f,"r") as fie:
           urls+=fie.read().splitlines()
with open("Combined_urls.txt","w") as resu:
    resu.write("\n".join(urls))