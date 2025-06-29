import os
import argparse

def main():

    if args.dire!="":
        direct=os.chdir(directory)
    else:
        direct=os.chdir("..\\")
    
    if args.ur:
        urls=[]
        for f in os.listdir():
            if "urls_" in f:
               with open(f,"r") as fie:
                   urls+=fie.read().splitlines()
        with open("Combined_urls.txt","w") as resu:
            resu.write("\n".join(urls))
    if args.sent:
        direct=os.chdir("SENT_TO_DOWNLOAD")
        sen=[]
        for f in os.listdir():
           with open(f,"r") as fie:
               sen+=fie.read().splitlines()
        with open("Combined_SENT_TO_DOWN.txt","w") as resu:
            resu.write("\n".join(sen))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Combine_urls - совместить все строки из файлов')
    parser.add_argument('--urls', dest='ur', default='0', metavar='0', help='Пройти через все urls выше папкой на одну',type=int)
    parser.add_argument('--dir', dest='dire', default='', metavar='""', help='в какой папке искать (relative path), по дефолту выбирает выше корнем',type=str)
    parser.add_argument('--sent_to', dest='sent', default='0', metavar='0', help='SENT_TO_DOWNLOAD folder combine everything in one',type=int)
    args = parser.parse_args()
    main()