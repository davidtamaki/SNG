from textblob import TextBlob
from sngsql.stop import stop
import re
import time


# counts consecutive repeating chars for emphasis ( >=3 )
def consecutive(string):
        if re.search(r'(.)\1\1', string):
            return True
        else:
            return False


t = time.process_time() # T start
tb1 = TextBlob("Awesomeeeee news!!!! Bernie's dogsss aren't probably the BEST Challengers Hillary Could've Hoped for http://t.co/GC9O81Dt2m http://t.co/6KvEPDhahw")
# tb2 = TextBlob("Me and Rick Perry are reeeel good budies http://t.co/9syhZfo9GA")

print (str(tb1))
print (tb1.sentiment)
# print (tb1.correct)
# print (tb1.words)
# print (tb1.tags)


# for added emphasis to scoring
points=0
for w in tb1.words:
    w.correct()
    if w.isupper():
        print ('upper case word found: ' + str(w))
        points+=1
    if consecutive(w):
        print ('found >3 cons chars.. ' + str(w))
        points+=1

print (str(points))




# for loading into db

urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(tb1))
print (urls)

words = tb1.words
words.singularize()
#words.remove(urls)

# remove short words, stop words, and urls
words = [w for w in tb1.words if len(w)>2 and w not in (stop or urls)] 
print (words)


elapsed_time = time.process_time() - t # T end
print ('time (sec): ' + str(elapsed_time) + '\n')





                # pre-sentiment score:
                # smily faces
                # stretch out common slang (e.g. LOL = laughing out loud)
             

                # Pre-storage:

                # clean punctuation
                # capitalisation
                # remove symbols
                # remove hashtags
                # remove urls
                # pluralisation?
                # correct spelling


