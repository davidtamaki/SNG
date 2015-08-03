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


# reduces consecutive repeating chars >3 to 2 (e.g. cooooool -> cool)
def consecutive(string):
    sub = re.findall(r'((\w)\2{2,})', string)
    if not sub:
        return string
    else:
        # print ('REPEATING CHAR SUBSTITION: ' + string)
        x=0
        while x<len(sub):
            string = string.replace(sub[x][0], sub[x][1]+sub[x][1])
            x+=1
        return string

# removes unicode
def remove_emoji(string):
    try:
        # Wide UCS-4 build
        myre = re.compile(u'['
            u'\U0001F300-\U0001F64F'
            u'\U0001F680-\U0001F6FF'
            u'\u2600-\u26FF\u2700-\u27BF]+', 
            re.UNICODE)
    except re.error:
        # Narrow UCS-2 build
        myre = re.compile(u'('
            u'\ud83c[\udf00-\udfff]|'
            u'\ud83d[\udc00-\ude4f\ude80-\udeff]|'
            u'[\u2600-\u26FF\u2700-\u27BF])+', 
            re.UNICODE)
    return myre.sub('', string)

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