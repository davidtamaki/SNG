from textblob import TextBlob
from sngsql.stop import stop
import re


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
# input TextBlob object, output list of words and list of urls
def clean_words(TB):
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(TB))
    shoutouts_and_hashtags = [w[1:] for w in str(TB).split() if (w[0]=='@' or w[0]=='#')]
    #shoutouts_and_hashtags = [str(TextBlob(s).words.singularize()) for s in shoutouts_and_hashtags]
    print ('shoutouts and hashtags: ' + str(shoutouts_and_hashtags))
    #words = TB.words.singularize()
    words = TB.words
    
    # remove short words, stop words, and urls
    remove=[]
    for u in urls:
        remove.append([w for w in words if w in u])
    remove = [u for url in remove for u in url]
    stopwords = [w for w in words if w in stop]
    remove = remove + stopwords + shoutouts_and_hashtags
    print (remove)

    words = [w.lower() for w in words if len(w)>2 and w not in (remove)] 
    print (words)
    return words






