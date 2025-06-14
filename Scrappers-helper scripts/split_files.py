files=10

with open("urls.txt","r") as file:
    urls=file.read().splitlines()

coef=len(urls)//files


for i in range(files):
    with open("file_"+str(i)+".txt","w") as file1:
        if i!=files-1:
            file1.write("\n".join(urls[coef*(i):coef*(i+1)]))
        else:
            file1.write("\n".join(urls[coef*(i):]))