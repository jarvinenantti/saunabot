from bs4 import BeautifulSoup
from time import sleep
from time import localtime
from dateutil.relativedelta import relativedelta
from crypting import write_key, load_key, encrypt, decrypt


# URL for login-page
hrefL = "https://booking.hoas.fi/auth/login"
# URL for sauna calendar
hrefC = "https://booking.hoas.fi/varaus/service/timetable/331/"

localtm = localtime()


# Open sauna reservation system
def openSauna(web, filename, key):

    # Open login page
    web.go_to(hrefL)
    sleep(1)

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
    web.go_to(hrefC)

    # Open developer view, not working???
    web.press(web.Key.CONTROL + web.Key.SHIFT + "i")

    # # Export my calendar reservations
    # url2 = 'https://booking.hoas.fi/varaus/export/calendar/personal_feed/63146/fi/c91b6832f7e5770112a86689799ea766'
    # r2 = requests.get(url2)
    # html_content2 = r2.text
    # soup2 = BeautifulSoup(html_content2,"html.parser")


# Return sauna source soup
def returnSauna(web):

    source = web.get_page_source()
    source_soup = BeautifulSoup(source, "html.parser")

    return(source_soup)


# Move into the day of interest, eats date
def wantedDay(web, wantDay):

    strd = format(wantDay.day, '02')
    strm = format(wantDay.month, '02')
    stry = str(wantDay.year)
    href = hrefC+strd+'/'+strm+'/'+stry
    web.go_to(href)


# Move into the current day
def currentDay(web):

    # First check if need to turn back month in calendar
    parsed = returnSauna(web)
    try:
        toClick = parsed.find("a", class_="js-datepicker").string
        web.click(toClick)
        web.click()
        web.click(str(localtm.tm_mday))
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
        web.click(str(localtm.tm_mday))
    except Exception as e:
        print(e)
        print("Couldn't move into current day")


# Check whether own reservation at previous or next day, return boolean
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
    web.go_to(href)
    sleep(1)

    return success

# Try to reserve suitable reservation and return success state
def reserveSuitable(web, own_list, attr_list, m, attr_th):
    found = False
    success = False
    reservation = attr_list[0]

    for res in attr_list:
        if res.dt.month != m:  # Only check wanted month
            continue
        elif res.attr < attr_th:  # No suitable reservation, stop
            break
        else:
            found = True
            neighbors = hasNeighbors(own_list, res)
            two = twoPerWeek(own_list, res)
            if neighbors or two:  # Has neighbors, or enough per week
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