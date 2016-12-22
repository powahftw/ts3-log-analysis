#Log Analysis of a TeamSpeak Server with Python

I've started this project out of personal curiosity.
I hang out whith some of my friends on a private teamspeak and i wanted to find out more about the usage of it.
I was expecially interested on the frequency of connection and on the usual connection time.
I'll explore different question in the future, whith maybe more enphasis on the visual rappresentation of it!

I won't be able to provide the source file, but it's a simple .log file generated from a teamspeak files.

The data gathered is from a bit less than a month in September
We start from a uncleaned log files taken directly from the server and read it line by line
```
FILE_PATH = "ts3log.log"

with open(FILE_PATH, 'r', encoding="utf8") as f: # Open the raw log files and read the lines
    lines = f.readlines()
```	
By looking at the .log file we can see a lot of rubbish not really useful for our exploration
I've decided to clean it up using both a blacklist and whitelist, so i easily change the filter in the next future
```
blacklist_word = ["|permission 'b", "b_virtualserver_", "|file upload"]
whitelist_word = ["|client connected ", "|client disconnected "]

cleaned = []

for e in lines:  # Clean the list leaving only connection or disconnection message. Some Unnecessary filtering just for making sure of...
    if any(good_word in e for good_word in whitelist_word) and not any(bad in e for bad in blacklist_word):
```
We now keep only the connection and disconnection of users to work whith. Since they are separated the best way to work whith them would be to pair them 
I've created a custom class for storing the session time and a list where i'm going to put all the sessions
```
class session():
    def __init__(self, user, connection, connection_time, disconnection_time):
        self.user = user
        self.connection = connection
        self.connection_time = connection_time
        self.disconnection_time = disconnection_time
        self.session_time = 0

    def print_info(self):
        print("User: {:42} \t {} {} \t {:10.2f} Min".format(self.user, self.connection_time, self.disconnection_time, self.session_time/60))
```		
		
		
Now here come a problem for the final result accuracy. The .log files doesn't show if a user change nickname during the session.
By pairing based on the nickname there could be some cases where the user connect whith "NICK1" changes to "NICK2" and for the log purposes he never logged out whith "NICK1"
Given the infrequency on which these behaviour appear i've simply decided to throw the result out, insted of having to manually pair each nickname whith all the variation my dear friends can came up whith.
```
import re

logs = []

def get_date(line):  # Get the time of dc/connection from a log line
    return line[0:19]

for e in cleaned:  # Create a list of classes instances where we put connection and disconnection together
    name = re.search("'(.*)'", e).group(1).split("'")[0]
    date = get_date(e)

    for i in logs:
        if i.user == name and i.connection == 0:
            i.connection = 1
            i.disconnection_time = date
            break

    if e[65:74]=="connected":
        k = session(name, 0, date, 0)
        logs.append(k)		
```
If there is a previous instance of connection it matches the two, otherwise it create a new one.
Now we remove all unclosed connection to fix the problem explained before
```
cleaned_logs = []

for e in logs: #Clean problem in the list of classes. People change nickname once connected and that causes problem
    if e.connection == 1:
        cleaned_logs.append(e)
```		
I've decided to add to the session the duration which it will be useful later

from datetime import datetime
```
def time_difference(line): #Find seconds between the start and end of a session
    d1 = datetime.strptime(line.connection_time, '%Y-%m-%d %H:%M:%S')
    d2 = datetime.strptime(line.disconnection_time, '%Y-%m-%d %H:%M:%S')
    return (d2 - d1).seconds
	
for e in cleaned_logs: #Find the time spent connected
    e.session_time = time_difference(e)
```	
Let's now have a look at some lines of results, i've created a function to print all session longer than a certain threshold
```
def print_list(session_list, value):
    for e in session_list:
        if e.session_time>value:
            e.print_info()
			
print_list(logs, 0)
```
```
"User: User1                                    	 2016-09-26 12:13:04 2016-09-26 20:50:24 	     517.33 Min
 User: User2                                     	 2016-09-26 12:22:17 2016-09-26 14:21:39 	     119.37 Min
 User: User3                                     	 2016-09-26 12:23:17 2016-09-26 12:23:22 	       0.08 Min"
 ```
Something to keep in mind is that the connection dime is different from effective presence. Some of my friends like to stay in the AFK room for hours.
Let's now look at the biggest connection recorded 
```
def most_connected(session_list):
    biggest_session = 0
    max = 0
    for e in session_list:
        if e.session_time > max:
            max = e.session_time
            biggest_session = e
            
    return biggest_session
	
most_connected((cleaned_logs)).print_info()	
```
```
"User: StrangeFriend1                                 	 2016-09-10 17:52:03 2016-09-16 17:49:51 	    1437.80 Min"
```
A bit shy of 6 days! It's a big number but as i said i had no way to check from the .log if the user didn't interact at all or kept talking for 5 straight days.
For those wondering about the possible accuracy of my result, here it is a more recent result from another user, directly from the TS3 stats panel

![example](http://i.imgur.com/qME5MyP.png)

To check other contender we might as well sort the entire log list based on the session_time 

```
import operator

sorted_cleaned_logs = sorted(cleaned_logs, key=operator.attrgetter('session_time'), reverse=True)
```
```
"User: StrangeFriend1                                 	 2016-09-10 17:52:03 2016-09-16 17:49:51 	    1437.80 Min
User: StrangeFriend2                                   	 2016-09-03 14:21:16 2016-09-04 13:58:13 	    1416.95 Min
User: StrangeFriend3                                     2016-09-08 23:58:28 2016-09-09 23:22:28 	    1404.00 Min"
```
As you could have guess the first result don't change. I still didn't expect such close second and third places.

I now might be interested in looking at the total time spend the Teamspeak Server by the user. I'll create a dictionary with nicknames as key and timespent as value.
```
def time_connected(list):
    d  = {}

    for e in list:
        if e.user in d:
            d[e.user] = e.session_time + d[e.user]
        else:
            d[e.user] = e.session_time

    return (d)

d0 = time_connected(cleaned_logs)
```
But that doesn't tell much without a relative value. Let's get a percentage on the timedelta of the logging.
```
def time_connected_percentage(dict, timedelta):
    for e in dict:
        dict[e] = (dict[e]/timedelta*100)
    return dict

d1 = time_connected_percentage(d0, timedelta)
```
Let's now look at some result. As expected user that have the habit of staying AFK for long period of time have a higher percentage of time connected.
```
"NiceFriend1                                    	: 4.80
StrangeFriend2                                   	: 16.84
NiceFriend2                                  	    : 3.29
PowahFTW                              	          : 4.97
NiceFriend3                                    	  : 0.22"
```
Since i never change the nickname and have the habit of disconnecting if i plan on staying long period of time afk i can say the data don't have much discrepancy in my case whith my expectation.

Last thing i wanted to know was the favorite hours of a user. It return the probability of fining someone at a certain time out of all the time he connected.
This is usefult to track favorite time of someone.
```
def probability(list,nick,target_time): #Print the probability of finding user at certain times out of all the times he connect

    count_pres = 0
    count_tot = 0
    for e in list:
        if e.user == nick:
            count_tot += 1
            inn = datetime.strptime(e.connection_time, '%Y-%m-%d %H:%M:%S')
            out = datetime.strptime(e.disconnection_time, '%Y-%m-%d %H:%M:%S')
            combined = str((str(e.connection_time[0:10])) + str(target_time))
            time = datetime.strptime(combined, '%Y-%m-%d%H:%M:%S')
            if inn < time < out:
                count_pres += 1

    if not count_pres:
        print("User not found in the log")
        return 0
    else:
        print ("{} is connected at {}:   {:.2s}% of times connected".format(nick,target_time, str(count_pres/count_tot*100)))
        return 1
```
Let's now look at a friend i know connect mostly during the evening.
```
probability(cleaned_logs, "EveningFriend", "21:30:00")

"EveningFriend is connected at 21:30:00:   29% of times connected"

probability(cleaned_logs, "EveningFriend", "8:30:00")

"EveningFriend is connected at 8:30:00:   1.1% of times connected"
```
That makes sense.

#Conclusion

Following [Peter Norving suggestion](http://norvig.com/spell-correct.html) i've then decided to test my procedure with another log files to making sure i was writing a code compatibile with all my server .log files and everything seems to work correctly.

In the future i'd like to make this script more user friendly and implement user tracking between multiple log files to have a better understanding of usage and habits. 
