# Implement reservation as a class with status, time and attractiveness
class Reservation:
    def __init__(self, own, free, dt, current, attr):
        self.own = own  # boolean
        self.free = free  # boolean
        self.dt = dt  # datetime
        self.current = current  # boolean, True for current month
        self.attr = attr  # int (0-10)

    def dispTime(self):
        print('Reservation datetime: '+str(self.dt))

    def calculateAttr(self):
        wkd = self.dt.weekday()
        h = self.dt.hour
        a = 0
        # weekday points
        if wkd == 6:  # Sun
            a += 5
        elif wkd == 5:  # Sat
            a += 3
        elif wkd == 4:  # Fri
            a += 3
        elif wkd == 3:  # Thu
            a += 4
        else:  # Wed
            a += 4
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
