# -*- coding: utf-8 -*-
"""
Webbot for Sauna reservations in HOAS reservation system

1) Login to HOAS reservations system and open reservations calendar
2) Check how many monthly reservations are left, if none -> do nothing
3) List all free reservations
4) Choose the best time(s) based on preferations
5) Make reservation(s) if there is an available time that fills criteria

Development steps:
- Move to cloud
- Add option to update unsuitable dates (e.g. via Telegram)

@author: ANTJA
"""
from crypting import write_key, load_key, encrypt, decrypt
from time import localtime
from datetime import date
from dateutil.relativedelta import relativedelta
import os as os
from resCal import reservationCal
import saunaTools as st
import listReservations as lr

#%%

# Define bot location and login info filename
# Windows
loc = os.getcwd()+"\\"
# Unix
# loc = os.getcwd()+"/"
filename = "login_info.txt"

# IF FIRST TIME: generate and write a new key (uncomment)
# write_key(loc)
# key = load_key(loc)
# encrypt(loc, filename, key)

# Define reservation attractiveness threshold on a scale of 0-10
attr_th = 8

localtm = localtime()

# Return True if next month is reservable
def nextMonthReservable():

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

    key = load_key(loc)

    # Open Sauna reservation system
    s = st.openSauna(loc, filename, key)

    # Check if reservations can be made for next month
    two_months = nextMonthReservable()

    # Find how many reservation are left, split to current and next month
    res_left = lr.reservationsLeft(s, two_months)

    # Return a list of all own reservations
    own_list = lr.ownReservations(s)

    # Return a list of all free reservations
    free_list = lr.freeReservations(s)

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
    excluded_free_list = lr.availableReservations(res_left,
                                                  own_list, free_list)

    # Return and print a list of possible reservations in attractiveness order
    attr_list = lr.showReturnPossibleReservations(excluded_free_list)

    # Reserve with attractiveness and calendar criterias
    # Return list of reserved reservations
    reserved = st.reserveSuitable(s, own_list, attr_list, attr_th, res_left)

    # Update calendar
    for res in reserved:
        resCal.addHour(res)

    # Terminate session, ok we are done!
    s.get('https://booking.hoas.fi/auth/logout')


if __name__ == "__main__":
    main()
