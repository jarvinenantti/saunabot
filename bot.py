# -*- coding: utf-8 -*-
"""
Webbot to make Sauna reservations in HOAS service

1) Login to HOAS reservations system
2) Open sauna reservations
3) Check how many monthly reservations are left, if not do nothing (print)
4) Open calendar and choose day based on preferations
5) Make reservation(s) if there is a time that fills preferations


Development
-Put login info to a crypted file
-If can't reserve for specific day, return and try other day
-Simultaneously, make day preferences more delicate
-How to run autonomously?
-Can this be imported to android?

Created on Wed Mar  4 09:58:47 2020

@author: ANTJA
"""

from webbot import Browser
import time
from datetime import date
from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup

# Check local time
tm = time.localtime()
year = tm[0]
month = tm[1]
day = tm[2]
hour = tm[3]
wkday = tm[6]

# Open sauna reservation system
def openSauna(web):
    print("Inside openSauna function")
    
    # Open login page
    web.go_to('https://booking.hoas.fi/auth/login')
    time.sleep(3)
    
    #Read login info file
    f = open("login_info.txt", "r")
    name = f.readline().split() # exclude \n
    psswd = f.readline()
    f.close()
    # Input username and password
    web.type(name[0] , into='login')
    web.type(psswd , into='password')
    #web.click('submit', tag='button')
    web.click('Kirjaudu')
    
    # Go to saunavuorot
    web.go_to('https://booking.hoas.fi/varaus/service/timetable/331/')
    
    # Open developer view, not working???
    web.press(web.Key.CONTROL + web.Key.SHIFT + 'i')

    ## Export my calendar reservations
    #url2 = 'https://booking.hoas.fi/varaus/export/calendar/personal_feed/63146/fi/c91b6832f7e5770112a86689799ea766'
    #r2 = requests.get(url2)
    #html_content2 = r2.text
    #soup2 = BeautifulSoup(html_content2,"html.parser")
    
    
def returnSauna(web):
    print("Inside returnSauna function")
    # Extract reservations source
    source = web.get_page_source()
    source_soup = BeautifulSoup(source,"html.parser")
    
    return(source_soup)


# Find and return how many reservations are left
def reservationsLeft(parsed):
    print("Inside reservationsLeft function")
    res_left = parsed.find_all("td", colspan="1") # type = ResultSet
    res_left_list = str(res_left[0]).split() # type = Tag ==> str ==> list
    used = int(res_left_list[5])
    limit = int(res_left_list[9][0])
    left = limit-used
    
    return(left)


# Choose the day to make reservation
# ADD SOME KIND OF CHECK TO THIS FUNCTION
def chooseDay(web):
    print("Inside chooseDay function")
    # Open calendar with local time
    if day < 10:
        str_day = "0"+str(day)
    else:
        str_day = str(day)
    if month < 10:
        str_month = "0"+str(month)
    else:
        str_month = str(month)
    str_year = str(year)
    str_time_query = str_day+"."+str_month+"."+str_year
    web.click(str_time_query)
    time.sleep(3)

    # Make reservation(s)
    # weekdays available ==> reserve next weekend Sunday times
    if ((wkday < 5) or (wkday == 5 and hour < 21)):
        next_week_end = 14 - wkday
        sunday = str(date.today() + relativedelta(days=+next_week_end))[-2:]
        web.click(sunday) # change the day
    # Saturday available ==> reserve  nextnext Saturday times
    elif ((wkday < 6) or (wkday == 6 and hour < 21)):
        nextnext_week_end = 14
        saturday = str(date.today() + relativedelta(days=+nextnext_week_end))[-2:]
        web.click(saturday) # change the day
    # Sunday available ==> reserve nextnext Sunday times
    else:
        nextnext_week_end = 14
        sunday = str(date.today() + relativedelta(days=+nextnext_week_end))[-2:]
        web.click(sunday) # change the day
    time.sleep(3)
        

# Reservation function, return True if succesfull
def reserve(web,parsed):
    print("Inside reserve function")
    
    # Find if there is reservations left
    opens = parsed.find_all("a", title="Varaa") # type = ResultSet
    if len(opens) == 0:
        return(False)
    
    # Print the times in reverse order for reservations
    for i in range(len(opens)-1,0,-1):    
        opens_list = str(opens[i]).split() # type = Tag ==> str ==> list
        res_time = int(opens_list[3][:2])
        print(str(res_time))
        
    # Reserve the LAST time
    # CREATE BETTER LOGIC FOR THIS
    web.click("Vapaa", number=len(opens))
    web.click("Varaa")
    
    return True
    
def main():
    print("Inside main function")
    
    # Make instance of browser
    web = Browser()
    
    # Open Sauna reservation system
    openSauna(web)
    
    # Return Sauna source soup
    parsed = returnSauna(web)
    
    # Find how many reservation are left
    res_left = reservationsLeft(parsed)
    
    # If left, make reservation
    if res_left > 0:
        print("Reservations left "+ str(res_left))
        # Choose the day
        chooseDay(web)
        # Return new Sauna source soup
        parsed2 = returnSauna(web)
        # Make reservation with new source data
        success = reserve(web,parsed2)
        if success == True:
            print("Reservation made")
        else:
            print("Reservation not possible for the day")
    else:
        print("No reservation left, do nothing")
    
if __name__ == "__main__":
         main()
        
