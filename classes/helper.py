import math


def round_two_digits(num):
    num = int(num)
    if num == 0:
        return 0
    else:
        scale = int(math.log10(abs(num)))
        num_rounded = round(num, -scale + 1)
        return num_rounded


def round_kmm(num):
    if num == 0:
        return "0"
    else:
        meter_rounded = round_two_digits(num)
        km = math.floor(meter_rounded / 1000)
        m = meter_rounded - 1000 * km
        hm = round(m/100)

        if km == 0:
            return f"{m}m"
        else:
            if hm == 0:
                return f"{km}km"
            else:
                return f"{km}.{hm}km"
