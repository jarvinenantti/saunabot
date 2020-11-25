from bs4 import BeautifulSoup
from time import sleep
from time import localtime
import datetime
from dateutil.relativedelta import relativedelta
from selenium.webdriver.common.keys import Keys
from crypting import write_key, load_key, encrypt, decrypt
from reservation import Reservation


# URL for login-page
hrefL = "https://booking.hoas.fi/auth/login"
# URL for sauna calendar
hrefC = "https://booking.hoas.fi/varaus/service/timetable/331/"

localtm = localtime()


#%%
# Open sauna reservation system
def openSauna(web, loc, filename, key):

    # Open login page
    web.get(hrefL)
    sleep(0.5)

    # Read login info file
    # decrypt the file
    decrypt(loc, filename, key)
    f = open(loc+filename, "r")
    name = f.readline().split()  # exclude \n
    psswd = f.readline()
    f.close()
    # encrypt the file
    encrypt(loc, filename, key)

    # Input username
    elem = web.find_element_by_name("login")
    elem.send_keys(name[0])
    # and password
    elem = web.find_element_by_name("password")
    elem.send_keys(psswd)
    web.find_elements_by_xpath("//input[@value='Kirjaudu']")[0].click()

    # Go to saunavuorot
    web.get(hrefC)

    # # Export my calendar reservations
    # url2 = 'https://booking.hoas.fi/varaus/export/calendar/personal_feed/63146/fi/c91b6832f7e5770112a86689799ea766'
    # r2 = requests.get(url2)
    # html_content2 = r2.text
    # soup2 = BeautifulSoup(html_content2,"html.parser")


# Return sauna source soup
def returnSauna(web):

    source = web.page_source
    source_soup = BeautifulSoup(source, "html.parser")

    return(source_soup)


# Move into the day of interest, eats date
def wantedDay(web, wantDay):

    strd = format(wantDay.day, '02')
    strm = format(wantDay.month, '02')
    stry = str(wantDay.year)
    href = hrefC+strd+'/'+strm+'/'+stry
    web.get(href)


# Move into the current day
def currentDay(web):

    toAdd = str(localtm.tm_mday)+"/"+str(localtm.tm_mon)+"/"+str(localtm.tm_year)
    href = hrefC+toAdd
    try:
        web.get(href)
        sleep(0.5)
    except Exception as e:
        print(e)
        print("Couldn't move into the current day")


# Check whether own reservation at same, previous or next day, return boolean
def hasNeighbors(own_list, res):
    hasN = False

    # Previous and following date
    y_date = res.dt.date()
    yminus1 = y_date + relativedelta(days=-1)
    yplus1 = y_date + relativedelta(days=+1)

    for r in own_list:
        x_date = r.dt.date()
        if x_date == y_date or x_date == yminus1 or x_date == yplus1:
            hasN = True
            print(str(r.dt)+" has neighbors")

    return(hasN)


# Check whether two or more reservations in same week, return boolean
def twoPerWeek(own_list, res):

    count = 0
    r_WN = res.dt.isocalendar()[1]
    for own in own_list:
        o_WN = own.dt.isocalendar()[1]
        if o_WN == r_WN:
            count += 1

    return (count >= 2)


# Check whether the reservation is the wanted, and return boolean
def wantedHour(tag, searchTime):
    return (tag.attrs["data-date"] == searchTime)


# Reservation function, return True if succesfull
def reserve(web, res):
    success = False

    # Open the wanted day
    wantedDay(web, res.dt)

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
    web.get(href)
    sleep(0.5)

    return success


# Try to reserve suitable reservations, and return list of reserved
def reserveSuitable(web, own_list, attr_list, attr_th, res_left):
    reserved = []

    found = False
    success = False
    currentM = datetime.date.today().month
    counter = currentM
    for left in res_left:
        if left == 0:
            print("No reservations left for month "+str(counter))
            found = False
            success = False
        else:
            found = False
            for res in attr_list:
                success = False
                if res.dt.month != counter:  # Only check wanted month
                    continue
                elif res.attr < attr_th:  # No suitable reservations
                    continue
                else:
                    neighbors = hasNeighbors(own_list, res)
                    two = twoPerWeek(own_list, res)
                    if neighbors or two:  # Has neighbors, or enough per week
                        continue
                    else:
                        found = True
                        print('Suitable reservation found')
                        res.dispTime()
                        success = reserve(web, res)
                        if success:  # Succesfully reserved -> save to list
                            reserved.append(res)
                            own_list.append(res)
                            print("Succesfully reserved")
                            continue
                        else:
                            print("Reservation found, but not succesfully reserved")
            if not(found):
                m = (datetime.date.today() + relativedelta(months=counter+1)).month
                print("No suitable reservations for month "+str(m))
        counter += 1

    return reserved
