files=15
file_name='..\\BOOKS TO DOWNLOAD\\batch_2.txt'

with open(file_name,"r") as file:
    urls=file.read().splitlines()

coef=len(urls)//files

folder="..\\BOOKS TO DOWNLOAD\\"
name=file_name.split(".txt")[0]
for i in range(files):
    with open(folder+name+"_file_"+str(i)+".txt","w") as file1:
        if i!=files-1:
            file1.write("\n".join(urls[coef*(i):coef*(i+1)]))
        else:
            file1.write("\n".join(urls[coef*(i):]))