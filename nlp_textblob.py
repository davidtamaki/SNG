from textblob import TextBlob
from words import *
import re
import string
from config import *
from helper import *



# for loading into db
# input dirty words list(punctuation and urls removed), output final words list
def clean_words(words_input,hashtags,shoutouts): 
    remove = [w.lower() for w in words_input if binarySearch(STOP, w.lower())] + hashtags + shoutouts
    words = [w for w in words_input.lower() if w not in remove]
    words = [consecutive(w) for w in words]
    words = [w for w in words if len(w)>2]
    print ('words: ' + str(words))
    return words


# clean tweet before applying sentiment analysis
# input dirty string, output dictionary for nlp analysis results
def analyse_tweet(tweetstring,expanded_url):
    print ('expanded_urls: ' + str(expanded_url))

    # remove tinyurl from tweetstring
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweetstring)
    for u in urls:
        tweetstring = tweetstring.replace(u,'')

   # hashtag and shoutout analysis
    hashtags = []
    shoutouts = []
    for word in tweetstring.split():
        if word[0] == '#':
            hashtags.append(word[1:].lower())
        if word[0] == '@':
            shoutouts.append(word[1:].lower())
    hashtags = [h.translate(str.maketrans("", "", string.punctuation)) for h in hashtags]
    shoutouts = [s.translate(str.maketrans("", "", string.punctuation)) for s in shoutouts]
    print ('hashtags: ' + str(hashtags))
    print ('shoutouts: ' + str(shoutouts))

    # ! implies pos / neg sentiment 93% of time
    if '!' in tweetstring:
        print ('"!" FOUND - SHOULD NOT BE + or -')

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

    # auto-score for key hashtags
    if hashtags:
        for h in hashtags:
            if h in CANDIDATE_HASHTAGS:
                contestant = CANDIDATE_HASHTAGS[h]['Name']
                sentiment = CANDIDATE_HASHTAGS[h]['Sentiment']
                team = CANDIDATE_USERNAMES[contestant]['Party']
                print ('Candidate Hashtag identified: ' + str(h))
                return ({'sentiment':sentiment, 'team':team, 'hashtags':hashtags, 'shoutouts': shoutouts,
                    'urls':urls, 'contestant':contestant, 'tb_sentiment': tb_sentiment, 
                    'tb_subjectivity': TB.sentiment.subjectivity, 'tb_polarity': TB.sentiment.polarity, 'tb_words': TB.words})
    
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


    # sentiment analysis
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


    return ({'sentiment':sentiment, 'team':team, 'hashtags':hashtags, 'shoutouts': shoutouts,
        'urls':urls, 'contestant':contestant, 'tb_sentiment': tb_sentiment, 
        'tb_subjectivity': TB.sentiment.subjectivity, 'tb_polarity': TB.sentiment.polarity, 'tb_words': TB.words})







