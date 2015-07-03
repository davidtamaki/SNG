# popular words
SELECT word, count(word) 
FROM word
GROUP BY word
HAVING count(word)>1
ORDER BY count(word) DESC

# average sentiment scores of contestants
select contestant, round(cast(avg(polarity) as numeric),2), count(polarity) as total,
	count(case when sentiment ='negative' then sentiment else null end) as negative,
	count(case when sentiment ='neutral' then sentiment else null end) as neutral,
	count(case when sentiment ='positive' then sentiment else null end) as positive
from item
group by contestant
order by avg(polarity) desc


# important users with counts and no of posts
select uid, screen_name, followers_count, friends_count, count(message)
from "user"
join item on item.user_id="user".id
where followers_count > '10000'
or friends_count > '10000'
group by uid, screen_name, followers_count, friends_count
order by count(message) desc


# show all users with more than 1 post
SELECT user_id, screen_name,
	COUNT(user_id) AS user_count 
FROM item JOIN "user" ON item.user_id = "user".id
GROUP BY user_id, screen_name
HAVING COUNT(user_id) > 1
ORDER BY user_count DESC
ORDER BY user_count DESC

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