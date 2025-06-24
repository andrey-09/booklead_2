import datetime
from internetarchive.session import ArchiveSession
import time
import matplotlib.pylab as plt
amount_of_hours=1



def monitoring_history(amount_of_hours):
    
    with open("history_Archive.txt","r") as file:
        history=file.read().splitlines()
    
    
    history = {value.split(" ")[0]: int(value.split(" ")[1]) for value in history}
    
    s = ArchiveSession()
    
    right_now=datetime.datetime.today()-datetime.timedelta(hours=2) #2hours difference
    one_hour_before=right_now-datetime.timedelta(hours=amount_of_hours) 
    right_now=right_now.strftime('%Y-%m-%dT%H:%M:%SZ')
    one_hour_before=one_hour_before.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    search = s.search_items('uploader:"pavelserebrjanyi@gmail.com" AND addeddate:['+one_hour_before+" TO "+ right_now+"]")
    count=0
    for item in search:
        count+=1
    history[right_now]=count
    
    
    lists = sorted(history.items()) # sorted by key, return a list of tuples
    x, y = zip(*lists) # unpack a list of pairs into two tuples
    plt.figure(figsize=(20,6))
    plt.title("hourly (values show of the previous hour)")
    
    plt.plot([a.split("T")[1][:-4] for a in x], y, "*")
    plt.tight_layout()
    #plt.show()  
    plt.savefig('Monitoring Archive-org.png')

    #write history to a file:
    with open("history_Archive.txt","w") as file:
        for key, value in history.items():
            file.write(key)
            file.write(" ")
            file.write(str(value)+"\n")

#
monitoring_history(amount_of_hours)
"""
while True:
    
    print("Waiting 1 hour:")
    dt_future = datetime.datetime.now() + datetime.timedelta(hours=1)
    
    while datetime.datetime.now() < dt_future:
        time.sleep(300) 
    
    
    print("Data Saved")





"""