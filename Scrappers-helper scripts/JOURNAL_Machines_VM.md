# Journal of upload

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
## 28.6. 14:00-  (changed sem from 30 to 8 everywhere + downgrade to cheaper VMs + logs start from now!)


Cores: 
-Me: 10
Google CLoud Me: 8
Google Cloud Pete 8
Azure: 10
-> 36 threads each 8 semka -> 288requests at the same time




commands:
```shell
screen -r ...  
python booklead.py --list VM_2.txt --continue 1 --archive 1 --cores 8
```