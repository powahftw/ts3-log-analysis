# Code wrote to explore some of curiosity about my TS server. The code aim to format the data in a useful way and than answer some of my questions.
# It's based on a ipython notebook and the code aim to explore the data step-by-step so there is room for improvement performance-wise

import re
from datetime import datetime
import operator

# CONFIGURATION

FILE_PATH = "filepath.log"

BLACKLIST_WORD = ["|permission 'b", "b_virtualserver_", "|file upload"]
WHITELIST_WORD = ["|client connected ", "|client disconnected "]


class session():
    def __init__(self, user, connection, connection_time, disconnection_time):
        self.user = user
        self.connection = connection
        self.connection_time = connection_time
        self.disconnection_time = disconnection_time
        self.session_time = 0

    def print_info(self):
        print("User: {:42} \t {} {} \t {:10.2f} Min".format(self.user, self.connection_time, self.disconnection_time,
                                                            self.session_time / 60))


def print_list(session_list, value):
    for e in session_list:
        if e.session_time > value:
            e.print_info()


def print_dict(dict):
    for e in dict:
        print("{:42} \t: {:.2f}".format(e, dict[e]))


def time_connected(list):
    d = {}

    for e in list:

        if e.user in d:
            d[e.user] = e.session_time + d[e.user]
        else:
            d[e.user] = e.session_time

    return (d)


def time_connected_percentage(dict, timedelta):
    for e in dict:
        dict[e] = (dict[e] / timedelta * 100)
    return dict


def get_date(line):  # Get the time of dc/connection from a log line
    return line[0:19]


def time_difference(line):  # Find seconds between the start and end of a session
    d1 = datetime.strptime(line.connection_time, '%Y-%m-%d %H:%M:%S')
    d2 = datetime.strptime(line.disconnection_time, '%Y-%m-%d %H:%M:%S')
    return (d2 - d1).seconds


def main():
    with open(FILE_PATH, 'r', encoding="utf8") as f:  # Open the raw log files and read the lines
        lines = f.readlines()

    cleaned = []

    for e in lines:  # Clean the list leaving only connection or disconnection message. Some Unnecessary filtering just for making sure of...
        if any(good_word in e for good_word in WHITELIST_WORD) and not any(bad in e for bad in BLACKLIST_WORD):
            cleaned.append(e)

    logs = []

    for e in cleaned:  # Create a list of classes instances where we put connection and disconnection together
        name = re.search("'(.*)'", e).group(1).split("'")[0]
        date = get_date(e)

        for i in logs:
            if i.user == name and i.connection == 0:
                i.connection = 1
                i.disconnection_time = date
                break

        if e[65:74] == "connected":
            k = session(name, 0, date, 0)
            logs.append(k)

    cleaned_logs = []

    for e in logs:  # Clean problem in the list of classes. People change nickname once connected and that causes problem
        if e.connection == 1:
            cleaned_logs.append(e)

    for e in cleaned_logs:  # Find the time spent connected
        e.session_time = time_difference(e)

    # print_list(cleaned_logs, 0) Print list of people, filter by parameter the value under X

    def most_connected(session_list):
        biggest_session = 0
        max = 0
        for e in session_list:
            if e.session_time > max:
                max = e.session_time
                biggest_session = e

        return biggest_session

    def choice_menu():
        selection = int(input(
            "1 - Biggest connection\n2 - Print all session\n3 - Total Time connected (seconds)\n4 -  % Time connected\n5 - Probability certain times\n\n"))
        if selection < 1 or selection > 5:
            choice_menu()
        else:
            return selection

    while True:  # Menu
        i = choice_menu()
        if i == 1:
            most_connected((cleaned_logs)).print_info()
        if i == 2:
            threshold = abs(int(input("Threshold for displaying the session (seconds):\t")))
            sorted_cleaned_logs = sorted(cleaned_logs, key=operator.attrgetter('session_time'),
                                         reverse=True)  # Sort the list of connection in descending order based on session time
            print_list(sorted_cleaned_logs, threshold)  # Print all session which lasted more than 10 minutes in
        d0 = time_connected(
            cleaned_logs)  # Create a dictionary where there is name as key and time spent connection as key value
        if i == 3:
            print_dict(d0)
        if i == 4:
            timedelta = (datetime.strptime(get_date(lines[-1]), '%Y-%m-%d %H:%M:%S') - datetime.strptime(
                get_date(lines[0].replace(u'\ufeff', '')),
                '%Y-%m-%d %H:%M:%S')).total_seconds()  # Timedelta between the start and end of logging period. A bit messy
            d1 = time_connected_percentage(d0,
                                           timedelta)  # Create a dictionary where there is name as key and time spent as % of the period as key value
            print_dict(d1)  # Print the dictionary
        if i == 5:
            def probability(list, nick,
                            target_time):  # Print the probability of finding user at certain times out of all the times he connect

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
                    print("{} is connected at {}   {:.2s}% of times connected".format(nick, target_time, str(
                        count_pres / count_tot * 100)))
                    return 1

            username = str(input("Username to check"))
            timetocheck = str(input("Time to check, use HH:MM:SS format"))
            probability(cleaned_logs, username, timetocheck)

        if input("Insert X to QUIT").lower() == "x":
            quit()


if __name__ == main():
    main()
