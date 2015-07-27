# connect user and hashtag
select screen_name,hashtag
from user_hashtag
join "user" on user_hashtag.user_id="user".id
join hashtag on user_hashtag.hashtag_id=hashtag.id

# connect user and word
select screen_name,word
from user_word
join "user" on user_word.user_id="user".id
join word on user_word.word_id=word.id

# connect item and hashtag
select item.item_id,hashtag
from item_hashtag
join item on item_hashtag.item_id=item.id
join hashtag on item_hashtag.hashtag_id=hashtag.id

# connect item and word
select item.item_id,word
from item_word
join item on item_word.item_id=item.id
join word on item_word.word_id=word.id

# connect user and hashtag
select screen_name,hashtag
from user_hashtag
join "user" on user_hashtag.user_id="user".id
join hashtag on user_hashtag.hashtag_id=hashtag.id
where hashtag = 'tcot'
order by hashtag

select screen_name,word
from user_word
join "user" on user_word.user_id="user".id
join word on user_word.word_id=word.id
join item on item.user_id="user".id
group by screen_name,word
having count(item_id)>5


#find smily faces :)
select *
from item
where message similar to '%:\)%'


# unicode faces range
select *
from item
where message similar to '%[\U0001F600-\U0001F6FF]%'


# messages with questions
select item_id, message, sentiment, polarity
from item
where message similar to '%\?%'


# select items by date
select * from item
WHERE date::date = '2015-07-13'
WHERE date::date = current_date-1


# popular urls
SELECT url, count(url) AS count
FROM url
GROUP BY url
HAVING count(url)>1
ORDER BY count(url) DESC


# tweets with data on hashtags
select contestant, sentiment, round(cast(polarity as numeric),2) as polarity, share_count, message
from item_hashtag
join item on item_hashtag.item_id=item.id
join hashtag on item_hashtag.hashtag_id=hashtag.id
where hashtag = 'Clinton'


# average sentiment scores of contestants
SELECT contestant,
	ROUND(100*SUM(CASE WHEN sentiment_textblob ='negative' THEN share_count ELSE NULL END)/SUM(share_count),2) AS pc_negative_tb,
	ROUND(100*SUM(CASE WHEN sentiment ='negative' THEN share_count ELSE NULL END)/SUM(share_count),2) AS pc_negative,
	ROUND(100*SUM(CASE WHEN sentiment_textblob ='neutral' THEN share_count ELSE NULL END)/SUM(share_count),2) AS pc_neutral_tb,
	ROUND(100*SUM(CASE WHEN sentiment ='neutral' THEN share_count ELSE NULL END)/SUM(share_count),2) AS pc_neutral,
	ROUND(100*SUM(CASE WHEN sentiment_textblob ='positive' THEN share_count ELSE NULL END)/SUM(share_count),2) AS pc_positive_tb,
	ROUND(100*SUM(CASE WHEN sentiment ='positive' THEN share_count ELSE NULL END)/SUM(share_count),2) AS pc_positive,
	COUNT(share_count) AS tweet_count,
	SUM(share_count) AS total_retweet_count
FROM item
WHERE date > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
GROUP BY contestant
HAVING SUM(share_count) > 100
ORDER BY pc_positive DESC


# polarity of each hashtag for each contestant
SELECT contestant,
	ROUND(100*SUM(CASE WHEN sentiment_textblob ='negative' THEN 1 ELSE NULL END)/COUNT(share_count),2) AS pc_negative_tb,
	ROUND(100*SUM(CASE WHEN sentiment_textblob ='neutral' THEN 1 ELSE NULL END)/COUNT(share_count),2) AS pc_neutral_tb,
	ROUND(100*SUM(CASE WHEN sentiment_textblob ='positive' THEN 1 ELSE NULL END)/COUNT(share_count),2) AS pc_positive_tb,
	ROUND(100*SUM(CASE WHEN sentiment ='negative' THEN 1 ELSE NULL END)/COUNT(share_count),2) AS pc_negative,
	ROUND(100*SUM(CASE WHEN sentiment ='neutral' THEN 1 ELSE NULL END)/COUNT(share_count),2) AS pc_neutral,
	ROUND(100*SUM(CASE WHEN sentiment ='positive' THEN 1 ELSE NULL END)/COUNT(share_count),2) AS pc_positive,
	COUNT(share_count) AS tweet_count,
	SUM(share_count) AS total_retweet_count
FROM item_hashtag
JOIN item ON item_hashtag.item_id=item.id
JOIN hashtag ON item_hashtag.hashtag_id=hashtag.id
WHERE hashtag = 'stoprush'
GROUP BY contestant
ORDER BY pc_positive DESC


# basic time series plot of retweet count
select contestant,
	sum(case when date::date = current_date then share_count else null end) as today,
	sum(case when date::date = current_date-1 then share_count else null end) as yesterday,
	sum(case when date::date = current_date-2 then share_count else null end) as twodaysago,
	sum(case when date::date = current_date-3 then share_count else null end) as threedaysago,
	sum(case when date::date = current_date-4 then share_count else null end) as fourdaysago,
	sum(share_count) as total
from item
group by contestant
having sum(share_count)>10000


# important users with counts and no of posts
select uid, screen_name, followers_count, friends_count, count(message)
from "user"
join item on item.user_id="user".id
where followers_count > '20000'
group by uid, screen_name, followers_count, friends_count
order by count(message) desc


# show all users with more than 1 post
SELECT user_id, screen_name, followers_count,
	COUNT(user_id) AS user_count 
FROM item JOIN "user" ON item.user_id = "user".id
GROUP BY user_id, screen_name, followers_count
HAVING COUNT(user_id) > 1
ORDER BY followers_count DESC


# items with both Clinton and Trump (comparative sentences)
select contestant, item_id, message, sentiment, polarity, date
from item
group by contestant, item_id, message, sentiment, polarity, date
having message ilike ('%Clinton%')
and message ilike ('%Trump%')
and message not in (select message
	from item
	group by message
	having message ilike ('%Hillary Clinton%')
	and message ilike ('%Donald Trump%'))


# show retweet growth for tweets (created yesterday or today)
SELECT rt.item_id, creation_date, date_time, elapsed_time, rt.share_count, item_url
FROM retweet_growth AS rt
JOIN item ON item.item_id=rt.item_id
WHERE rt.item_id IN 
	(SELECT item_id
	FROM retweet_growth
	GROUP BY item_id
	HAVING count(item_id)>1)
AND creation_date::date >= current_date-1
ORDER BY item_id, date_time, share_count


# verified user tweets
select contestant, screen_name, date, item_id, followers_count, share_count, message, item_url, sentiment
from "user"
join item on item.user_id="user".id
where verified_user = true
order by date::DATE DESC, contestant


# grouped items by expanded urls
SELECT contestant, date, item_id, group_item_id, favorite_count, share_count, message, item_url, sentiment, polarity, source
FROM item
WHERE item_id IN
	(SELECT DISTINCT ON (group_item_id) item_id
	FROM item
	WHERE sentiment = 'positive'
	AND date > (CURRENT_TIMESTAMP - interval '24 hours')
	ORDER BY group_item_id)
ORDER BY share_count DESC



# update fav / share count
UPDATE item SET favorite_count = '2000', share_count = '1800' WHERE item_id= '617592269621694464';
UPDATE item SET favorite_count = '2000', share_count = '1800' WHERE item_id= '617527052086976512';

UPDATE item SET group_item_id=item_id 

# remove data with foreign key constraints
DELETE FROM item_word WHERE item_id IN (SELECT id FROM item where contestant similar to '%[\U0001F44D-\U0001F6FF]%');
DELETE FROM item_hashtag WHERE item_id IN (SELECT id FROM item where contestant similar to '%[\U0001F44D-\U0001F6FF]%');
DELETE FROM item WHERE contestant similar to '%[\U0001F44D-\U0001F6FF]%';

CREATE TEMPORARY TABLE old_items AS SELECT id, item_id FROM item WHERE date < (CURRENT_TIMESTAMP - INTERVAL '5 days');
DELETE FROM item_word WHERE item_id IN (SELECT id FROM old_items);
DELETE FROM item_hashtag WHERE item_id IN (SELECT id FROM old_items);
DELETE FROM retweet_growth WHERE item_id IN (SELECT item_id FROM old_items);
DELETE FROM url WHERE item_id IN (SELECT item_id FROM old_items);
DELETE FROM item WHERE item_id IN (SELECT item_id FROM old_items);
DISCARD TEMP;

# db size
select t1.datname AS db_name,  
       pg_size_pretty(pg_database_size(t1.datname)) as db_size
from pg_database t1
order by pg_database_size(t1.datname) desc;


