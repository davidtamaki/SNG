from textblob import TextBlob
from sngsql.words import *
import re
import string
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
# input dirty words list(punctuation and urls removed), output final words list
def clean_words(words_input,hashtags):
    # shoutouts_and_hashtags = [w for w in words_input if (w[0]=='@' or w[0]=='#')]
    remove = [w for w in words_input if binarySearch(STOP, w.lower())] + hashtags
    words = [w for w in words_input.lower() if len(w)>2 and w not in remove] 
    return words


# clean tweet before applying sentiment analysis
# input dirty string, output dictionary for nlp analysis results
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
    hashtags = [h.translate(str.maketrans("", "", string.punctuation)) for h in hashtags]
    print ('hashtags: ' + str(hashtags))

    #remove punctuation
    tweetstring = tweetstring.translate(str.maketrans("", "", string.punctuation))

    # tb sentiment
    TB = TextBlob(tweetstring)
    if TB.sentiment.polarity < 0:
        tb_sentiment = "negative"
    elif TB.sentiment.polarity == 0:
        tb_sentiment = "neutral"
    else:
        tb_sentiment = "positive"

    # d_hashtags = False
    # r_hashtags = False
    if hashtags:
        for h in hashtags:
            # if h in DEMOCRAT:
            #     d_hashtags = True
            # if h in REPBLICAN:
            #     r_hashtags = True
            if h in CANDIDATE_HASHTAGS:
                contestant = CANDIDATE_HASHTAGS[h]['Name']
                sentiment = CANDIDATE_HASHTAGS[h]['Sentiment']
                team = CANDIDATE_USERNAMES[contestant]['Party']
                print ('Candidate Hashtag identified: ' + str(h))
                return ({'sentiment':sentiment, 'team':team, 'hashtags':hashtags, 
                    'urls':urls, 'contestant':contestant, 'tb_sentiment': tb_sentiment, 
                    'tb_subjectivity': TB.sentiment.polarity, 'tb_polarity': TB.sentiment.polarity, 'tb_words': TB.words})
    
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

    team = CANDIDATE_USERNAMES[contestant]['Party']

    # if d_hashtags or r_hashtags:
    #     print ('Political party candidate found')
    #     if team = 'Democrat' and d_hashtags:
    #         sentiment = 'positive'
    #     elif team = 'Democrat' and r_hashtags:
    #         sentiment = 'negative'
    #     elif team = 'Republican' and d_hashtags:
    #         sentiment = 'negative'
    #     elif team = 'Republican' and r_hashtags:
    #         sentiment = 'positive'
    #     return ({'sentiment':sentiment, 'team':team, 'hashtags':hashtags, 
    #         'urls':urls, 'contestant':contestant, 'tb_sentiment': tb_sentiment, 
    #         'tb_subjectivity': TB.sentiment.polarity, 'tb_polarity': TB.sentiment.polarity, 'tb_words': TB.words})


    # sentiment analysis
    # length = len(TB.words)
    p, n = 0, 0
    negation_rule = False
    for word in TB.words:
        if word.lower() in NEGATION:
            negation_rule = True
            continue
        if binarySearch(POSITIVE, word.lower()):
            if negation_rule == True:
                n+=1
                negation_rule = False
                continue
            p+=1
            continue
        elif binarySearch(NEGATIVE, word.lower()):
            if negation_rule == True:
                p+=1
                negation_rule = False
                continue
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


    return ({'sentiment':sentiment, 'team':team, 'hashtags':hashtags, 
        'urls':urls, 'contestant':contestant, 'tb_sentiment': tb_sentiment, 
        'tb_subjectivity': TB.sentiment.polarity, 'tb_polarity': TB.sentiment.polarity, 'tb_words': TB.words})







