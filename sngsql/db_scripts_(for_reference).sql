
# show all users with more than 1 post
SELECT user_id, screen_name,
	COUNT(user_id) AS user_count 
FROM Tweet JOIN "user" ON Tweet.user_id = "user".id
GROUP BY user_id, screen_name
HAVING COUNT(user_id) > 1
ORDER BY user_count DESC

# connect tweets and words via tweet_word
SELECT * 
FROM tweet_word JOIN word ON tweet_word.word_id=word.id
	JOIN tweet ON tweet_word.tweet_id=tweet.id
WHERE user_id = 41



select screen_name,hashtag
from user_hashtag
join "user" on user_hashtag.user_id="user".id
join hashtag on user_hashtag.hashtag_id=hashtag.id

select item.item_id,hashtag
from item_hashtag
join item on item_hashtag.item_id=item.id
join hashtag on item_hashtag.hashtag_id=hashtag.id

select item.item_id,word
from item_word
join item on item_word.item_id=item.id
join word on item_word.word_id=word.id

select screen_name,word
from user_word
join "user" on user_word.user_id="user".id
join word on user_word.word_id=word.id