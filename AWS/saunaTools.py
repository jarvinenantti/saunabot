from bs4 import BeautifulSoup
from time import sleep
from time import localtime
import datetime
import requests
import logging, lxml.html
from dateutil.relativedelta import relativedelta
from crypting import write_key, load_key, encrypt, decrypt
from reservation import Reservation

# URL for login-page
hrefL = "https://booking.hoas.fi/auth/login"
# URL for sauna calendar
hrefC = "https://booking.hoas.fi/varaus/service/timetable/331/"

localtm = localtime()

# enable debug logging with basic logging config
logging.basicConfig(level=logging.DEBUG)  


#%%
def openSauna(loc, filename, key):
    '''Open the sauna reservation system.
    Input file location, name and key.
    Return session.'''

    # Read login info file
    # decrypt the file
    decrypt(loc, filename, key)
    f = open(loc+filename, "r")
    name = f.readline().split()[0]  # exclude \n
    psswd = f.readline()
    f.close()
    # encrypt the file
    encrypt(loc, filename, key)

    # Open login page and input username and password
    s = requests.session()

    # Here, we're getting the login page and then grabbing hidden form
    # fields.  We're probably also getting several session cookies too
    login = s.get(hrefL)
    login_html = lxml.html.fromstring(login.text)
    hidden_inputs = login_html.xpath(r'//form//input[@type="hidden"]')
    form = {x.attrib["name"]: x.attrib["value"] for x in hidden_inputs}

    # Now that we have the hidden form fields, let's add in our username and
    # password
    form['login'] = name
    form['password'] = psswd
    response = s.post(hrefL, data=form)
    assert response.url != hrefL  # Throw error if login not succesful

    # Try opening reservation system
    sauna = s.get(hrefC)
    if sauna.status_code != requests.codes.ok:
        sauna.raise_for_status()

    # # Export my calendar reservations
    # url = 'https://booking.hoas.fi/varaus/export/calendar/personal_feed/63146/fi/c91b6832f7e5770112a86689799ea766'
    # r = requests.get(url)
    # html_content = r.text
    # soup = BeautifulSoup(html_content,"html.parser")

    return s


def returnSauna(s, href):
    '''Return sauna source soup, input session and url.'''

    source = s.get(href)
    if source.status_code != requests.codes.ok:
        source.raise_for_status()
    source_soup = BeautifulSoup(source.text, "html.parser")

    return(source_soup)


def wantedDay(wantDay):
    '''Return the full URL-path of wanted day, input date.'''

    strd = format(wantDay.day, '02')
    strm = format(wantDay.month, '02')
    stry = str(wantDay.year)
    href = hrefC+strd+'/'+strm+'/'+stry

    return(href)


def currentDay():
    '''Return the full url of the current day.'''

    strd = format(localtm.tm_mday, '02')
    strm = format(localtm.tm_mon, '02')
    stry = str(localtm.tm_year)
    href = hrefC+strd+'/'+strm+'/'+stry

    return(href)


def hasNeighbors(own_list, res):
    '''Check whether own reservation at same, previous or next day.
    Input own reservations list and reservation, return boolean.'''

    hasN = False

    # Previous and following date
    y_date = res.dt.date()
    yminus1 = y_date + relativedelta(days=-1)
    yplus1 = y_date + relativedelta(days=+1)

    # Check if near days match
    for r in own_list:
        x_date = r.dt.date()
        if x_date == y_date or x_date == yminus1 or x_date == yplus1:
            hasN = True
            print(str(r.dt)+" has neighbors")

    return(hasN)


def twoPerWeek(own_list, res):
    '''Check whether two or more reservations exists in same week.
    Input own reservation list and reservation, return boolean.'''

    count = 0
    r_WN = res.dt.isocalendar()[1]
    # Go through all own reservations
    for own in own_list:
        o_WN = own.dt.isocalendar()[1]
        if o_WN == r_WN:
            count += 1

    return (count >= 2)


def wantedHour(tag, searchTime):
    '''Check whether the reservation is the wanted.
    Input tag and searched time, return boolean.'''

    return (tag.attrs["data-date"] == searchTime)



def reserve(s, res):
    '''Reservation function. Input session and reservation, return boolean.'''

    success = False

    # URL of the wanted day
    href = wantedDay(res.dt)

    # Return Sauna source soup
    parsed = returnSauna(s, href)

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

    # Make reservation by using the reservation link
    r = s.get(href)
    if r.status_code != requests.codes.ok:
        r.raise_for_status()
    sleep(0.5)

    return success


# Try to reserve suitable reservations, and return list of reserved
def reserveSuitable(s, own_list, attr_list, attr_th, res_left):
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
                        success = reserve(s, res)
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
