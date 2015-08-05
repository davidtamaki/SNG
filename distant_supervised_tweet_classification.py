import json, time, re, datetime, math, requests
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from nlp_textblob import *
from words import *
from config import *
from helper import *


def get_wordcount_data():
	engine = create_engine('postgresql://sngsql:sngsql@127.0.0.1/tweet_classification')
	db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
	sql = (
		'''DISCARD TEMP;
		CREATE TEMPORARY TABLE total AS SELECT COUNT(word) AS a
		FROM item_word JOIN item ON item_word.item_id=item.id JOIN word ON item_word.word_id=word.id;
		CREATE TEMPORARY TABLE pos AS SELECT COUNT(word) AS p
		FROM item_word JOIN item ON item_word.item_id=item.id JOIN word ON item_word.word_id=word.id
		WHERE sentiment= 'positive';
		CREATE TEMPORARY TABLE neg AS SELECT COUNT(word) AS n
		FROM item_word JOIN item ON item_word.item_id=item.id JOIN word ON item_word.word_id=word.id
		WHERE sentiment= 'negative';
		CREATE TEMPORARY TABLE neu AS SELECT COUNT(word) AS n
		FROM item_word JOIN item ON item_word.item_id=item.id JOIN word ON item_word.word_id=word.id
		WHERE sentiment= 'neutral';
		SELECT word, 
			COUNT(word) AS count_total,
			ROUND(100*COUNT(word)/(SELECT a FROM total)::NUMERIC,6) AS pc_total,
			COUNT(CASE WHEN sentiment ='negative' THEN 1 ELSE NULL END) AS count_neg,
			ROUND(100*COUNT(CASE WHEN sentiment ='negative' THEN 1 ELSE NULL END)/(SELECT n FROM neg)::NUMERIC,6) AS pc_neg,
			COUNT(CASE WHEN sentiment ='positive' THEN 1 ELSE NULL END) AS count_pos,
			ROUND(100*COUNT(CASE WHEN sentiment ='positive' THEN 1 ELSE NULL END)/(SELECT p FROM pos)::NUMERIC,6) AS pc_pos,
			COUNT(CASE WHEN sentiment ='neutral' THEN 1 ELSE NULL END) AS count_neu,
			ROUND(100*COUNT(CASE WHEN sentiment ='neutral' THEN 1 ELSE NULL END)/(SELECT n FROM neu)::NUMERIC,6) AS pc_neu
		FROM item_word JOIN item ON item_word.item_id=item.id JOIN word ON item_word.word_id=word.id
		GROUP BY word
		ORDER BY COUNT(word) DESC''')
	wordcount_data = array_to_dicts(db_session.execute(sql))

	wc_data = {}
	for row in wordcount_data:
		wc_data[row['word']] = {'count_total': row['count_total'], 'pc_total': row['pc_total'],
		'count_neg': row['count_neg'], 'pc_neg': row['pc_neg'],	'count_pos': row['count_pos'],
		'pc_pos': row['pc_pos'], 'count_neu': row['count_neu'], 'pc_neu': row['pc_neu']}
	return wc_data


# input word list, output hash of bayes score for pos, neg, neu
def accumulate_prob(hash_wordcount,words):
	# SELECT COUNT(item) FROM item
	# GROUP BY sentiment

	# prior probability for each category (50,000 items of each)
	prior_pos = (50000/125000)
	prior_neg = (50000/125000)
	prior_neu = (25000/125000)

	log_prob_pos = 0.0
	log_prob_neg = 0.0
	log_prob_neu = 0.0

	for w in words:
		# skip words not in hash
		if w not in hash_wordcount:
			continue
		w_hash = hash_wordcount[w]
		# calculate the probability that the word occurs at all
		p_word = float(w_hash['pc_total'])
		# for both categories, calculate P(word|category), or the probability a 
		# word will appear, given that we know that the document is <category>
		p_w_given_pos = float(w_hash['pc_pos'])
		p_w_given_neg = float(w_hash['pc_neg'])
		p_w_given_neu = float(w_hash['pc_neu'])
		# add new probability to our running total: log_prob_<category>
		if p_w_given_pos > 0:
			log_prob_pos += math.log(p_w_given_pos / p_word)
		if p_w_given_neg > 0:
			log_prob_neg += math.log(p_w_given_neg / p_word)
		if p_w_given_neu > 0:
			log_prob_neu += math.log(p_w_given_neu / p_word)

	# print out the results; we need to go from logspace back to "regular" space
	print ("Score(pos)  : ", math.exp(log_prob_pos + math.log(prior_pos)))
	print ("Score(neg)  : ", math.exp(log_prob_neg + math.log(prior_neg)))
	print ("Score(neu)  : ", math.exp(log_prob_neu + math.log(prior_neu)))

	prob_scores = ([['positive', math.exp(log_prob_pos + math.log(prior_pos))],
		['negative', math.exp(log_prob_neg + math.log(prior_neg))]])
		# ['neutral', math.exp(log_prob_neu + math.log(prior_neu))]])
	most_likely = max(prob_scores, key=lambda x: x[1])
	return most_likely[0]




if __name__ == '__main__':
	t = time.process_time()
	word_hash = get_wordcount_data()
	print (len(word_hash))
	elapsed_time = time.process_time() - t
	print ('wordcount hash creation: ' + str(elapsed_time) + '\n')




