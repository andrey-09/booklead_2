# Journal of Upload

Specs:
Azure (2CPU, 4GB Ram, 64 GB os)   
Google Cloud_Pete: (2CPU, 4GB Ram, 80 GB os)  
Cloud_Me:   

## 28.6.25 at 14:00 (everything in screen and in virtual env)
- Google Cloud_me -24 hours - 260 books (9305 timeout)
- Me: 12 hours - 160 boks (5000 Timeout)
- Azure: 24 hours: 327 b 5584 timeout; 5000 502 er ()
- Pete_Cloud: 48 hours: 1088 books; 21310 timeout; 30661 err
--------------------
## 28.6. 14:00-  (changed semka from 30 to 8 everywhere + downgrade to cheaper VMs + logs start from now!)
Cores: 
-Me: 10
Google CLoud Me: 8
Google Cloud Pete 8 (5 hours 600 502 servers; 40 matches TimeoutError )
Azure: 10
-> 36 threads each 8 semka -> 288 requests at the same time


## Total max requetsts check:
https://inforost.org/ru/nodes/127-litsenzionnaya-stoimost-platformy-inforost
"big library" is considered about 5000 books -> 1mil pages -> 1 - 2 TB) - price tag: 880,000 per year
-> 8k euros per year. (too much, 1-2 HDD costs 100$ -> to host +configure it another 100-200$. -that is it really!) 

Total requests simultarneous: 160 (tested, works)
(more than 300 starts breaking) #more than 200 simultaneous, constant errors 
(100-150ish easy) # https://loadster.app/dashboard
### specs: 1 hour: 80 books	
az ssh vm --resource-group min_group --vm-name min --subscription 0aadc356-6c58-45da-bfe1-59d430776658


commands:
```shell
screen -r ...  
python booklead.py --list VM_2.txt --continue 1 --archive 1 --cores 8
```

### Hosting Options:  
my data: 30 TB
Cloud hosting per TB: 23 $ (Amazon) - with HDD's also 20$ -> 600 $ all storage -> 60,000 RUB + hosting etc.

IA has 10PB of books -> 10,000 TB -> 
200,000 $ hosting (with 20$ per TB HDD) + hosting the website etc. -> 
Total about 20,000,000 RUB. (for 40 mill texts)