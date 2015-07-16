from textblob import TextBlob
from sngsql.words import *
import re
from config import *
from helper import *


# added emphasis to scoring
# input TextBlob object, output revised polarity score
# def emphasis(TB):
#     # print (TB.sentiment.polarity) 
#     if TB.sentiment.polarity!=0:
#         points=0
#         for w in TB.words:
#             if w.isupper():
#                 # print ('upper case word found: ' + str(w))
#                 points+=1
#             if consecutive(w):
#                 # print ('found >3 consecutive chars.. ' + str(w))
#                 points+=1

#         # print (str(points))
#         polarity = TB.sentiment.polarity * min(2,(1 + (points/10)))
#         if abs(polarity)>1:
#             polarity = polarity / abs(polarity)
#         return polarity
#     else:
#         return 0


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
# input dirty string, output dictionary for (sentiment, team, hashtags, urls, and contestant)
def analyse_tweet(tweetstring,expanded_url):
    print ('expanded_urls: ' + str(expanded_url))

    # remove tinyurl from tweetstring
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweetstring)
    for u in urls:
        tweetstring = tweetstring.replace(u,'')

    # hashtag analysis
    hashtags = []
    for word in tweetstring.split():
        if word[0] == '#':
            hashtags.append(word[1:].lower())
    print ('hashtags: ' + str(hashtags))
    if hashtags:
        for h in hashtags:
             # if hashtag is xyz2016, set instant sentiment and return
            if h in CANDIDATE_HASHTAGS:
                contestant = CANDIDATE_HASHTAGS[h]['Name']
                sentiment = CANDIDATE_HASHTAGS[h]['Sentiment']
                team = CANDIDATE_USERNAMES[contestant]['Party']
                print ('Candidate Hashtag identified: ' + str(h))
                print (contestant)
                return ({'sentiment':sentiment, 'team':team, 
                    'hashtags':hashtags, 'urls':urls, 'contestant':contestant })
    
    TB = TextBlob(tweetstring)

    # tag contestant
    contestant = None
    for x in SEARCH_TERM:
        if all (n.lower() in TB.words.singularize().lower() for n in x.split()):
            print (x)
            contestant = str(x)
            break
    if contestant is None and expanded_url is not None:
        # print ('searching url...')
        for x in SEARCH_TERM:
            if all (n.lower() in expanded_url for n in x.split()):
                print (x)
                contestant = str(x)
                break
    if contestant is None:
        # print ('searching any match...')
        for x in SEARCH_TERM:       
            if any (n.lower() in TB.words.lower() for n in x.split()):
                print (x)
                contestant = str(x)
                break
    if contestant is None:
        return ({'contestant': None})

    # need to compare multiple candidates in message

    # set team to candidate's party
    team = CANDIDATE_USERNAMES[contestant]['Party']

    # sentiment analysis
    p, n = 0, 0
    negation_rule = False
    for word in TB.words:
        # words strips out emoticons (only matches emoji)
        # if word in POS_EMOJI:
        if word.lower() in NEGATION:
            # print ('negation word: ' + word)
            negation_rule = True
            continue
        if binarySearch(POSITIVE, word.lower()):
            if negation_rule == True:
                # print ('negation on pos: ' + word)
                n+=1
                negation_rule = False
                continue
            # print ('pos: ' + word)
            p+=1
            continue
        elif binarySearch(NEGATIVE, word.lower()):
            if negation_rule == True:
                # print ('negation on neg: ' + word)
                p+=1
                negation_rule = False
                continue
            # print ('neg: ' + word)
            n+=1
            continue
        else:
            negation_rule = False

    print ('positive = ' + str(p) + '   negative = ' + str(n))
    if p>n:
        sentiment='positive'
    elif n>p:
        sentiment='negative'
    else:
        sentiment='neutral'

    return ({'sentiment':sentiment, 'team':team,
        'hashtags':hashtags, 'urls':urls, 'contestant':contestant })







