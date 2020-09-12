# -*- coding: utf-8 -*-
"""
Webbot for Sauna reservations in HOAS reservation system

1) Login to HOAS reservations system
2) Open sauna reservations
3) Check how many monthly reservations are left, if none -> do nothing
4) Open calendar and choose best day based on user preferations
5) Make reservation(s) if there is a time that fills criteria

Development directions
- Change reservation.date to date object ERROR TRACK
- Create exe-file
- Run cron script autonomously on Raspberry Pi

@author: ANTJA
"""
from crypting import write_key, load_key, encrypt, decrypt
from webbot import Browser
from time import localtime
from time import sleep
from datetime import date
from datetime import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup
import calendar as cd

# Track function calls
function_calls = False

# IF FIRST TIME: generate and write a new key (uncomment)
# write_key()
# encrypt(filename, key)

# Define reservation attractiveness threshold on scale of 0-10
attr_th = 8

# Check local time -> global user session time
localtm = localtime()
year = localtm.tm_year
month = localtm.tm_mon
day = localtm.tm_mday
hour = localtm.tm_hour
wkday = localtm.tm_wday
# Get week number
a_date = date(year, month, day)
weekN = a_date.isocalendar()[1]


# To hold HOAS reservations three datetime categories are required:
# 1) Week (2-3 weeks, can be separated between months)
# 2) Day (1-7 days)
# 3) Hours are included as reservation attribute
class reservationCal:
    def __init__(self, weeks):
        self.weeks = weeks

    # Add (if necessary) and return the week and order number
    def addWeek(self, Week):
        try:
            # If empty or largest week -> append and return
            if len(self.weeks) == 0 or Week.wN > self.weeks[len(self.weeks)-1].wN:
                self.weeks.append(Week)
                oN = len(self.weeks)-1
                return([self.weeks[oN], oN])
            for i in range(len(self.weeks)):
                # If week already exists -> return
                if Week.wN == self.weeks[i].wN:
                    return(self.weeks[i], i)
                # If new but not largest week -> insert and return
                if Week.wN < self.weeks[i].wN:
                    self.weeks.insert(i, Week)
                    return(self.weeks[i], i)
        except Exception as e:
            print(e)
            print('Failed to add new week')

    def addHour(self, res):
        try:
            y = res.dt.year
            m = res.dt.month
            d = res.dt.day
    
            # Add (if necessary) and return week and order number
            res_date = date(y, m, d)
            wN = res_date.isocalendar()[1]
            weekToAdd = self.Week(wN, [])
            [weekX, wON] = self.addWeek(weekToAdd)
    
            # Add (if necessary) and return the day and order number
            wdN = cd.weekday(y, m, d)
            dayToAdd = self.Week.Day(wdN, m, [])
            [dayX, dON] = weekX.addDay(dayToAdd)
    
            # Add (or replace) the reservation, True if added, False if replaced
            status = self.weeks[wON].days[dON].addReservation(res)
            return status
        except Exception as e:
            print(type(e))
            print(e.args)  # arguments stored in .args
            print(e)
            print('Failed to add new hour')

    class Week:
        def __init__(self, wN, days):
            # Week number
            self.wN = wN  # int
            # List of days in week
            self.days = days  # list

        # Add (if necessary) and return the day and order number
        def addDay(self, Day):
            try:
                # If empty or largest day -> append and return
                if len(self.days) == 0 or Day.wdN > self.days[len(self.days)-1].wdN:
                    self.days.append(Day)
                    oN = len(self.days)-1
                    return([self.days[oN], oN])
                for i in range(len(self.days)):
                    # If day already exists -> return
                    if Day.wdN == self.days[i].wdN:
                        return([self.days[i], i])
                    # If new but not largest day -> insert and return
                    if Day.wdN < self.days[i].wdN:
                        self.days.insert(i, Day)
                        return([self.days[i], i])
            except Exception as e:
                print(e)
                print('Failed to add day')
    
        class Day:
            def __init__(self, wdN, mN, reservations):
                # Weekday number
                self.wdN = wdN  # int
                # Month number
                self.mN = mN  # int
                # List of daily reservations
                self.reservations = reservations  # list
    
            def addReservation(self, Reservation):
                try:
                    # If largest hour -> append
                    if len(self.reservations) == 0 or Reservation.dt.hour > self.reservations[len(self.reservations)-1].dt.hour:
                        self.reservations.append(Reservation)
                    for i in range(len(self.reservations)-1):
                        # If reservation already exists -> break
                        if Reservation.dt.hour == self.reservations[i].dt.hour:
                            self.reservations[i] = Reservation
                        # If new but not largest reservation -> insert
                        if Reservation.dt.hour < self.reservations[i].dt.hour:
                            self.reservations.insert(i, Reservation)
                except Exception as e:
                    print(e)
                    print('Failed to add reservation')


# day1 = Week.Day(3, month, [])
# day2 = Week.Day(4, month, [])
# week1 = Week(weekN, [])
# week1.insertDay(day1)
# week1.insertDay(day2)
# resCal = reservationCal([])
# res1 = Reservation(True, True, datetime(2020, 9, 10, 18), True, 10)
# resCal.addHour(res1)
# res2 = Reservation(True, True, datetime(2020, 9, 9, 18), True, 10)
# resCal.addHour(res2)


# Implement reservation as a class with status, time and attractiveness
class Reservation:
    def __init__(self, own, free, dt, current, attr):
        self.own = own  # boolean
        self.free = free  # boolean
        self.dt = dt  # datetime
        self.current = current  # boolean, True for current month
        self.attr = attr  # int (0-10)

    def calculateAttr(self):
        wkd = self.dt.weekday()
        h = self.dt.hour
        a = 0
        # weekday points
        if wkd == 6:
            a += 5
        elif wkd == 5 or wkd == 4:
            a += 3
        else:
            a = a
        #  Time points
        if h == 20:
            a += 5
        elif h == 19:
            a += 4
        elif h == 21:
            a += 3
        elif h == 18:
            a += 2
        else:
            a = a
        self.attr = a


# Open sauna reservation system
def openSauna(web, filename, key):
    if function_calls: print("Inside openSauna function")

    # Open login page
    web.go_to("https://booking.hoas.fi/auth/login")
    sleep(3)

    # Read login info file
    # encrypt the file
    decrypt(filename, key)
    f = open(filename, "r")
    name = f.readline().split()  # exclude \n
    psswd = f.readline()
    f.close()
    # decrypt the file
    encrypt(filename, key)

    # Input username and password
    web.type(name[0], into="login")
    web.type(psswd, into="password")
    # web.click('submit', tag='button')
    web.click("Kirjaudu")

    # Go to saunavuorot
    web.go_to("https://booking.hoas.fi/varaus/service/timetable/331/")

    # Open developer view, not working???
    web.press(web.Key.CONTROL + web.Key.SHIFT + "i")

    # # Export my calendar reservations
    # url2 = 'https://booking.hoas.fi/varaus/export/calendar/personal_feed/63146/fi/c91b6832f7e5770112a86689799ea766'
    # r2 = requests.get(url2)
    # html_content2 = r2.text
    # soup2 = BeautifulSoup(html_content2,"html.parser")


# Return sauna source soup
def returnSauna(web):
    if function_calls: print("Inside returnSauna function")
    # Extract reservations source
    source = web.get_page_source()
    source_soup = BeautifulSoup(source, "html.parser")

    return(source_soup)


# Return True if next month is reservable
def nextMonthReservable(web):
    if function_calls: print("Inside nextMonthReservable function")

    reservable = False
    forward = 0  # how many days forward is last reservable
    if hour >= 21:
        forward = 15
    else:
        forward = 14
    lastAvailableDay = date.today() + relativedelta(days=+forward)
    if lastAvailableDay.month > month:
        reservable = True
        print("Reservations can be made also for next month")

    return reservable


# Move into day of interest
def wantedDay(web, wantDay):
    if function_calls: print("Inside wantedDay function")

    parsed = returnSauna(web)
    toClick = parsed.find("a", class_="js-datepicker").string
    web.click(toClick)
    web.click(str(wantDay))


# Move into current day
def currentDay(web):
    if function_calls: print("Inside currentDay function")

    # First check if need to turn back month in calendar
    parsed = returnSauna(web)
    try:
        toClick = parsed.find("a", class_="js-datepicker").string
        web.click(toClick)
        
        web.click()
        web.click(str(day))
    except Exception as e:
        print(e)
        print("Couldn't move into current day")

    parsed = returnSauna(web)
    try:
        # Open calendar
        toClick = parsed.find("a", class_="js-datepicker").string
        web.click(toClick)
        # Go back to current month if possible
        parsed = returnSauna(web)
        toClickM = parsed.find("span", class_="ui-icon ui-icon-circle-triangle-w").string
        web.click(toClickM, number=2)
        # Click back to current day
        web.click(str(day))
    except Exception as e:
        print(e)
        print("Couldn't move into current day")

    # first = False
    # try:
    #     while first is False:
    #         parsed = returnSauna(web)
    #         previous = parsed.find("a", class_="prev")
    #         if previous.attrs["style"] == "visibility: hidden;":
    #             #  Current day
    #             first = True
    #         else:
    #             web.click("Edellinen")
    #             sleep(1)
    # except Exception as e:
    #     print(e)
    #     print("Couldnt go back to current day")


# Find and return how many reservations are left to use
def reservationsLeft(web, two_months):
    if function_calls: print("Inside reservationsLeft function")

    parsed = returnSauna(web)

    left_current = -1
    left_next = -1

    # First check the current month
    try:
        # If Mon or Tue, go to Wed to see reservations left
        toClick = parsed.find("a", class_="js-datepicker").string
        if wkday < 2:
            move = 2-wkday
            web.click(toClick)
            web.click(str(day+move))
            sleep(2)
            parsed = returnSauna(web)

        res_left = parsed.find("td", colspan="1")  # tag
        text = str(res_left.contents[0])
        textList = text.split()
        used = int(textList[4])
        limit = int(textList[8])
        left_current = limit-used
        print("Reservations left for the current month: "+str(left_current))
    except Exception as e:
        print(e)
        print("Couldn't parse current month reservations left")

    if two_months:
        # Then check the next month
        try:
            forward = 0  # how many days forward is last reservable
            if hour >= 21:
                forward = 15
            else:
                forward = 14
            lastAvailableDay = date.today() + relativedelta(days=+forward)
            # If Mon or Tue, go back to Sunday
            if lastAvailableDay.weekday() < 2:
                lastAvailableDay = lastAvailableDay - relativedelta(days=+lastAvailableDay.weekday()+1)
            # Check again if Sunday is still in next month
            if lastAvailableDay.month == month:
                left_next == 0
            else:
                wantedDay(web, lastAvailableDay.day)
                parsed = returnSauna(web)
                toClick = parsed.find("a", class_="js-datepicker").string
                res_left = parsed.find("td", colspan="1")  # tag
                text = str(res_left.contents[0])
                textList = text.split()
                used = int(textList[4])
                limit = int(textList[8])
                left_next = limit-used
                print("Reservations left for the next month: "+str(left_next))
        except Exception as e:
            print(e)
            print("Couldn't parse next month reservations left")

    return(left_current, left_next)


# Find and return all own reservations
def ownReservations(web):
    if function_calls: print("Inside ownReservations function")
    own_list = []

    # Return Sauna source soup
    parsed = returnSauna(web)
    try:
        res_all = parsed.find_all("a", class_="sauna")
        for res in res_all:
            contents = res.string.split()
            d = int(contents[1][0:1])
            m = int(contents[1][3:5])
            y = int(contents[1][7:10])
            h = int(contents[2][0:1])
            if m == month:  # current month
                res = Reservation("True", "False", datetime(y, m, d, h),
                                  "True", 10)
            else:  # next month
                res = Reservation("True", "False", datetime(y, m, d, h),
                                  "False", 10)
            res.calculateAttr()
            own_list.append(res)
    except Exception as e:
        print(e)
        print("Couldn't parse own reservations")

    print(str(len(own_list))+" own reservations")
    return own_list


# Find and return all reservations of particular day
def listDayReservations(parsed):
    if function_calls: print("Inside listDayReservations function")
    res_list = []

    # Find if there is reservations left
    try:
        opens = parsed.find_all("a", title="Varaa")  # type = ResultSet
        if len(opens) == 0:
            print("All reserved")
        else:
            for open in opens:
                contents = open.attrs["data-date"].split()
                d = int(contents[0][0:2])
                m = int(contents[0][3:5])
                y = int(contents[0][6:10])
                h = int(contents[1][0:2])
                if m == month:  # current month
                    res = Reservation(False, True, datetime(y, m, d, h),
                                      "True", 10)
                else:  # next month
                    res = Reservation(False, True, datetime(y, m, d, h),
                                      "False", 10)
                res.calculateAttr()
                res_list.append(res)
    except Exception as e:
        print(e)
        print("Couldn't parse free reservations")

    return res_list


# Find and return all free reservations
def freeReservations(web):
    if function_calls: print("Inside freeReservations function")
    free_list = []

    #  Go to current day
    currentDay(web)

    last = False
    while last is False:
        # Return Sauna source soup
        parsed = returnSauna(web)
        try:
            #  Check if open reservations
            if len(parsed.find_all("a", title="Varaa")) > 0:
                free_list.append(listDayReservations(parsed))
            #  Check and change day
            following = parsed.find("a", class_="next")
            if following.has_attr("style") is True and following.attrs["style"] == "visibility: hidden;":
                #  Last day
                last = True
                sleep(1)
            else:
                web.click("Seuraava")
                sleep(1)

        except Exception as e:
            print(e)
            print("Couldn't parse free reservations")

    # Go back to current day
    currentDay(web)

    return free_list


# Find and return all free reservations, excluding days with own reservations
def availableReservations(res_left, own_list, free_list):
    if function_calls: print("Inside availableReservations function")
    excluded_free_list = []

    # Pop out reservations if no credits left
    counter = 0
    for day_list in free_list:
        if res_left[0] == 0 and int(day_list[0].dt.month) == month:
            del free_list[counter]
        if res_left[1] == 0 and int(day_list[0].dt.month) == month+1:
            del free_list[counter]
        counter += 1

    # Check if there is own reservation for the same day
    same_day = False
    for day_list in free_list:
        for own in own_list:
            if own.dt == day_list[0].dt:
                same_day = True
        # If match was not found, append
        if not same_day:
            excluded_free_list.append(day_list)
        same_day = False

    return excluded_free_list


# Print and return reservable times in attr-order
def showReturnPossibleReservations(excluded_free_list):
    if function_calls: print("Inside showReturnPossibleReservations function")

    # Create a new list:
    # 1) with flat hierarchy (no day lists)
    # 2) and sort (decreasing) according to attractiveness
    new_list = []
    for free_day in excluded_free_list:
        for free_hour in free_day:
            print(str(free_hour.dt.day)+" day at "+str(free_hour.dt.hour)
                  +" o'clock with attractiveness: "+str(free_hour.attr))
            new_list.append(free_hour)
    sorted_list = sorted(new_list, key=lambda x: x.attr, reverse=True)

    # # List of times to reserve with >= attr_th
    # toReserve_list = []
    # for res in sorted_list:
    #     if res.attr >= attr_th:
    #         print(res.date+" at "+res.time)
    #         toReserve_list.append(res)

    return(sorted_list)


#%%


# Check whether the reservation is the wanted
def wantedHour(tag, searchTime):
    if function_calls: print("Inside wantedHour function")
    return tag.attrs["data-date"] == searchTime


# Reservation function, return True if succesfull
def reserve(web, res):
    if function_calls: print("Inside reserve function")
    success = False

    # Open the wanted day
    wantedDay(web, str(res.dt.day))

    # Return Sauna source soup
    parsed = returnSauna(web)

    # Find if the reservation is still left
    href = ""
    try:
        opens = parsed.find_all("a", title="Varaa")  # type = ResultSet
        searchTime = res.dt.strftime("%d.%m.%Y")+" "+str(res.dt.hour)+":00 - "+str(res.dt.hour+1)+":00"
        for open in opens:
            if wantedHour(open, searchTime):
                print("Still reservable")
                href = open.attrs["href"]
                success = True

    except Exception as e:
        print(e)
        print("Couldn't parse reservations")

    # Make reservation by clicking the link
    web.go_to(href)
    sleep(1)

    return success


def hasNeighbors(own_list, res):
    hasN = False

    # Previous and following date
    y_date = res.dt.date()
    yminus1 = y_date + relativedelta(days=-1)
    yplus1 = y_date + relativedelta(days=+1)

    for r in own_list:
        x_date = r.dt.date()
        if x_date == yminus1 or x_date == yplus1:
            hasN = True

    return(hasN)


def reserveSuitable(web, own_list, attr_list, m):
    found = False
    success = False
    reservation = attr_list[0]

    for res in attr_list:
        if res.attr < attr_th and res.dt.month == m:  # No suitable reservation, stop
            found = False
            break
        else:
            found = True
            neighbors = hasNeighbors(own_list, res)
            if neighbors:  # Has neighbor days, try next
                continue
            else:
                print(res.dt)
                success = reserve(web, res)
                if success:  # Succesfully reserved, save and stop
                    reservation = res
                    break
                else:
                    print("Failed to reserve suitable time")

    return [found, success, reservation]


#%%


def main():
    if function_calls: print("Inside main function")

    key = load_key()
    filename = "login_info.txt"

    # Make instance of browser
    web = Browser()

    # Open Sauna reservation system
    openSauna(web, filename, key)

    # Check if reservations can be made for next month
    two_months = nextMonthReservable(web)

    # Find how many reservation are left, split to current and next month
    res_left = reservationsLeft(web, two_months)

    # Return a list of all own reservations
    own_list = ownReservations(web)

    # Return a list of all free reservations
    free_list = freeReservations(web)

    # Create a calendar with all reservations
    resCal = reservationCal([])
    # Fill with free reservations
    for day in free_list:
        for free in day:
            resCal.addHour(free)
    # and with own reservations
    for own in own_list:
        resCal.addHour(own)

    # Return a list of free reservations excluding:
    # 1) days with own reservations
    # 2) month without reservation credits
    excluded_free_list = availableReservations(res_left, own_list, free_list)

    # Return and print a list of possible reservations in attractiveness order
    attr_list = showReturnPossibleReservations(excluded_free_list)

    # Reserve with attractiveness and calendar criterias
    if res_left[0] > 0:
        [suitable, success, reservation] = reserveSuitable(web, own_list, attr_list, month)
        if suitable:
            if success:
                print("Reservation made for current month")
            else:
                print("Couldn't reserve any suitable time")
        else:
            print("No suitable reservations")
    elif res_left[1] > 0:
        [suitable, success, reservation] = reserveSuitable(web, own_list, attr_list, month+1)
        if suitable:
            if success:
                print("Reservation made for next month")
            else:
                print("Couldn't reserve any suitable time")
        else:
            print("No suitable reservations")
    else:
        print('No reservations left for either month')


if __name__ == "__main__":
    main()
