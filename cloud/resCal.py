from datetime import date
import calendar as cd

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
