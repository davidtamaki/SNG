from textblob import TextBlob
from sngsql.words import *
import re
from config import *


# counts consecutive repeating chars for emphasis ( >=3 )
def consecutive(string):
        if re.search(r'(.)\1\1', string):
            return True
        else:
            return False



# added emphasis to scoring
# input TextBlob object, output revised polarity score
def emphasis(TB):
    # print (TB.sentiment.polarity) 
    if TB.sentiment.polarity!=0:
        points=0
        for w in TB.words:
            if w.isupper():
                # print ('upper case word found: ' + str(w))
                points+=1
            if consecutive(w):
                # print ('found >3 consecutive chars.. ' + str(w))
                points+=1

        # print (str(points))
        polarity = TB.sentiment.polarity * min(2,(1 + (points/10)))
        if abs(polarity)>1:
            polarity = polarity / abs(polarity)
        return polarity
    else:
        return 0


# for loading into db
# input TextBlob object, output list of words
def clean_words(TB):
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(TB))
    shoutouts_and_hashtags = [w[1:] for w in str(TB).split() if (w[0]=='@' or w[0]=='#')]
    #shoutouts_and_hashtags = [str(TextBlob(s).words.singularize()) for s in shoutouts_and_hashtags]
    # print ('shoutouts and hashtags: ' + str(shoutouts_and_hashtags))
    #words = TB.words.singularize()
    words = TB.words
    
    # remove short words, stop words, and urls
    remove=[]
    for u in urls:
        remove.append([w for w in words if w in u])
    remove = [u for url in remove for u in url]
    stopwords = [w for w in words if w in STOP]
    remove = remove + stopwords + shoutouts_and_hashtags
    # print (remove)

    words = [w.lower() for w in words if len(w)>2 and w not in (remove)] 
    # print (words)
    return words


# clean tweet before applying sentiment analysis
# input dirty string, output clean TextBlob object
def preprocess_tweet(tweetstring):
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweetstring)
    for u in urls:
        tweetstring = tweetstring.replace(u,'')
    print (tweetstring)

    hashtags = []
    for word in tweetstring.split():
        if word[0] == '#':
            hashtags.append(word[1:].lower())
    print ('hashtags: ' + str(hashtags))
    if hashtags:
        for h in hashtags:
            if h in DEMOCRAT:
                print ('democrat tag: ' + h)
            elif h in REPUBLICAN:
                print ('republican tag ' + h)


    p, n = 0, 0
    for word in tweetstring.split():
        # words strips out emoticons (only matches emoji)
        if binarySearch(POSITIVE, word.lower()) or word in POS_EMOJI:
            print ('pos: ' + word)
            p+=1
        elif binarySearch(NEGATIVE, word.lower()) or word in NEG_EMOJI:
            print ('neg: ' + word)
            n+=1
    print ('positive = ' + str(p) + '   negative = ' + str(n))
    if p>n:
        print ('positive!')
    elif n>p:
        print ('negative!')
    else:
        print ('neutral!')










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



