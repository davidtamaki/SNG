import re


def serialise_value(value):
	if value is None:
		return None
	else:
		return str(value)

def row2dict(row):
    d = {}
    for column in row.keys():
        d[column] = serialise_value((getattr(row, column)))
    return d

#converting postgres array data to python dict
def array_to_dicts(array):
    return [row2dict(row) for row in array]


# counts consecutive repeating chars for emphasis ( >=3 )
def consecutive(string):
        if re.search(r'(.)\1\1', string):
            return True
        else:
            return False

# binary search
def binarySearch(alist, item):
    first = 0
    last = len(alist)-1
    found = False

    while first<=last and not found:
        midpoint = (first + last)//2
        if alist[midpoint] == item:
            found = True
        else:
            if item < alist[midpoint]:
                last = midpoint-1
            else:
                first = midpoint+1
    return found


#converts time delta to minutes
def td_to_minutes(td):
    return (td.days*1440)+(td.seconds//60)