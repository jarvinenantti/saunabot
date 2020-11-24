from time import localtime
from datetime import date
from dateutil.relativedelta import relativedelta
from time import sleep
from datetime import datetime
import saunaTools as st
from reservation import Reservation

localtm = localtime()


# Find and return how many reservations are left for use
def reservationsLeft(web, two_months):

    st.currentDay(web)
    parsed = st.returnSauna(web)

    left_current = -1
    left_next = -1

    # First check the current month
    try:
        # If Mon or Tue, go to Wed to see reservations left
        toClick = parsed.find("a", class_="js-datepicker").string
        if localtm.tm_wday < 2:
            move = (date.today()+relativedelta(days=+(2-localtm.tm_wday))).day
            web.find_elements_by_link_text(str(toClick))[0].click()
            sleep(0.5)
            web.find_elements_by_link_text(str(move))[0].click()
            sleep(0.5)
            parsed = st.returnSauna(web)

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
            if localtm.tm_hour >= 21:
                forward = 15
            else:
                forward = 14
            lastAvailableDay = date.today() + relativedelta(days=+forward)
            # If Mon or Tue, go back to Sunday
            if lastAvailableDay.weekday() < 2:
                lastAvailableDay = lastAvailableDay - relativedelta(days=+lastAvailableDay.weekday()+1)
            # Check again if Sunday is still in next month
            if lastAvailableDay.month == localtm.tm_mon:
                left_next == 0
            else:
                st.wantedDay(web, lastAvailableDay)
                parsed = st.returnSauna(web)
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
    own_list = []

    # Return Sauna source soup
    parsed = st.returnSauna(web)
    try:
        res_all = parsed.find_all("a", class_="sauna")
        for res in res_all:
            contents = res.string.split()
            d = int(contents[1][0:2])
            m = int(contents[1][3:5])
            y = int(contents[1][6:10])
            h = int(contents[2][0:2])
            if m == localtm.tm_mon:  # current month
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
                if m == localtm.tm_mon:  # current month
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
    free_list = []

    #  Go to current day
    st.currentDay(web)

    last = False
    while last is False:
        # Return Sauna source soup
        parsed = st.returnSauna(web)
        try:
            #  Check if open reservations
            if len(parsed.find_all("a", title="Varaa")) > 0:
                free_list.append(listDayReservations(parsed))
            #  Check and change day
            following = parsed.find("a", class_="next")
            if following.has_attr("style") is True and following.attrs["style"] == "visibility: hidden;":
                #  Last day
                last = True
                sleep(0.5)
            else:
                web.find_elements_by_link_text("Seuraava")[0].click()
                sleep(0.5)

        except Exception as e:
            print(e)
            print("Couldn't parse free reservations")

    # Go back to current day
    st.currentDay(web)

    return free_list


# Find and return all free reservations, excluding days with own reservations
def availableReservations(res_left, own_list, free_list):
    excluded_free_list = []

    # Pop out reservations if no credits left
    counter = 0
    for day_list in free_list:
        if res_left[0] == 0 and int(day_list[0].dt.month) == localtm.tm_mon:
            del free_list[counter]
        if res_left[1] == 0 and int(day_list[0].dt.month) == localtm.tm_monh+1:
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

    # Create a new list:
    # 1) with flat hierarchy (no day lists)
    # 2) and sort (decreasing) according to attractiveness
    new_list = []
    for free_day in excluded_free_list:
        for free_hour in free_day:
            print(str(free_hour.dt.day)+" day at "+str(free_hour.dt.hour)+" o'clock with attractiveness: "+str(free_hour.attr))
            new_list.append(free_hour)
    sorted_list = sorted(new_list, key=lambda x: x.attr, reverse=True)

    # # List of times to reserve with >= attr_th
    # toReserve_list = []
    # for res in sorted_list:
    #     if res.attr >= attr_th:
    #         print(res.date+" at "+res.time)
    #         toReserve_list.append(res)

    return(sorted_list)
