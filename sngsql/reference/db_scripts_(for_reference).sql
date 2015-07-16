# popular words
SELECT word, count(word) 
FROM word
GROUP BY word
HAVING count(word)>1
ORDER BY count(word) DESC


# avg sentiment by hashtag for each contestant
select hashtag, 
	round(cast(avg(polarity) as numeric),2) as polarity,
	count(polarity) as total,
	count(case when sentiment ='negative' then sentiment else null end) as negative,
	count(case when sentiment ='neutral' then sentiment else null end) as neutral,
	count(case when sentiment ='positive' then sentiment else null end) as positive,
	sum(share_count) as total_retweet_count
from item_hashtag
join item on item_hashtag.item_id=item.id
join hashtag on item_hashtag.hashtag_id=hashtag.id
where contestant = 'Donald Trump'
group by hashtag
order by sum(share_count) desc


# tweets with data on hashtags
select contestant, sentiment, round(cast(polarity as numeric),2) as polarity, share_count, message
from item_hashtag
join item on item_hashtag.item_id=item.id
join hashtag on item_hashtag.hashtag_id=hashtag.id
where hashtag = 'Clinton'


# average sentiment scores of contestants
SELECT contestant, ROUND(CAST(AVG(polarity) AS NUMERIC),2) AS avg_sentiment,
	SUM(CASE WHEN sentiment ='negative' THEN share_count ELSE NULL END) AS negative,
	SUM(CASE WHEN sentiment ='neutral' THEN share_count ELSE NULL END) AS neutral,
	SUM(CASE WHEN sentiment ='positive' THEN share_count ELSE NULL END) AS positive,
	SUM(share_count) AS total_retweet_count
FROM item
GROUP BY contestant
HAVING SUM(share_count) > 5000
ORDER BY SUM(share_count) DESC


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


# items with both Clinton and Trump (comparative sentences)
select contestant, item_id, message, sentiment, polarity, date
from item
group by contestant, item_id, message, sentiment, polarity, date
having message like ('%Clinton%')
and message like ('%Trump%')
and message not in (select message
	from item
	group by message
	having message like ('%Hillary Clinton%')
	and message like ('%Donald Trump%'))


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




# update fav / share count
UPDATE item SET favorite_count = '2000', share_count = '1800' WHERE item_id= '617592269621694464';
UPDATE item SET favorite_count = '2000', share_count = '1800' WHERE item_id= '617527052086976512';

# remove data with foreign key constraints
DELETE FROM item_word WHERE item_id IN (SELECT id FROM item where contestant similar to '%[\U0001F44D-\U0001F6FF]%');
DELETE FROM item_hashtag WHERE item_id IN (SELECT id FROM item where contestant similar to '%[\U0001F44D-\U0001F6FF]%');
DELETE FROM item WHERE contestant similar to '%[\U0001F44D-\U0001F6FF]%';

delete from retweet_growth where item_id = '325973644276809730';
delete from item_word where item_id in (select id from item where item_id = '325973644276809730');
delete from item where item_id = '325973644276809730';


