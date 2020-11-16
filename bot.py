# -*- coding: utf-8 -*-
"""
Webbot for Sauna reservations in HOAS reservation system

1) Login to HOAS reservations system
2) Open sauna reservations
3) Check how many monthly reservations are left, if none -> do nothing
4) Open calendar and choose best day based on user preferations
5) Make reservation(s) if there is a time that fills criteria

Bugs:

Development directions
- Requiremetns into own file
- Move into AWS


@author: ANTJA
"""
from crypting import write_key, load_key, encrypt, decrypt
from webbot import Browser
from time import localtime
from datetime import date
from dateutil.relativedelta import relativedelta
from resCal import reservationCal
import saunaTools as st
import listReservations as lr


# IF FIRST TIME: generate and write a new key (uncomment)
# write_key()
# encrypt(filename, key)

# Define reservation attractiveness threshold on a scale of 0-10
attr_th = 8

localtm = localtime()


# Return True if next month is reservable
def nextMonthReservable(web):

    reservable = False
    forward = 0  # how many days forward is last reservable
    if localtm.tm_hour >= 21:
        forward = 15
    else:
        forward = 14
    lastAvailableDay = date.today() + relativedelta(days=+forward)
    if lastAvailableDay.month > localtm.tm_mon:
        reservable = True
        print("Reservations can also be made for the next month")

    return reservable



#%%


def main():

    key = load_key()
    filename = "login_info.txt"

    # Make instance of browser
    web = Browser()

    # Open Sauna reservation system
    st.openSauna(web, filename, key)

    # Check if reservations can be made for next month
    two_months = nextMonthReservable(web)

    # Find how many reservation are left, split to current and next month
    res_left = lr.reservationsLeft(web, two_months)

    # Return a list of all own reservations
    own_list = lr.ownReservations(web)

    # Return a list of all free reservations
    free_list = lr.freeReservations(web)

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
    excluded_free_list = lr.availableReservations(res_left, own_list, free_list)

    # Return and print a list of possible reservations in attractiveness order
    attr_list = lr.showReturnPossibleReservations(excluded_free_list)

    # Reserve with attractiveness and calendar criterias
    month = localtm.tm_mon
    if res_left[0] > 0:
        [suitable, success, reservation] = st.reserveSuitable(web, own_list,
                                                              attr_list, month, attr_th)
        if suitable:
            if success:
                print("Reservation made for the current month")
            else:
                print("Couldn't reserve any suitable time")
        else:
            print("No suitable reservations")
    elif res_left[1] > 0:
        [suitable, success, reservation] = st.reserveSuitable(web, own_list,
                                                              attr_list, month+1, attr_th)
        if suitable:
            if success:
                print("Reservation made for the next month")
            else:
                print("Couldn't reserve any suitable time")
        else:
            print("No suitable reservations")
    else:
        print('No reservations left for either month')

    # Close the web session
    web.quit()


if __name__ == "__main__":
    main()
