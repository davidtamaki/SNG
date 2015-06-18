from instagram.client import InstagramAPI
import json

client_id = '6a0d5f0482ff497a857a6dc5782e50ca'
client_secret = '8f927e97421c44a69c5891f2f3c4c08a'
access_token = '7237927.6a0d5f0.9c1ac2eb39c24f368bdbf6645a9ffcbc'
client_ip = '86.128.185.8'
api = InstagramAPI(client_id=client_id, client_secret=client_secret,client_ips= client_ip,access_token= access_token)





recent_media, next_ = api.tag_recent_media(tag_name='jonsnow', count=2) #change count
for item in recent_media:
    #print (dir(item.user))
    print (item.type)
    print (item.tags)
    print (item.comment_count)
    print (item.caption.text)
    print (item.like_count)
    print (item.link)
    print (item.user.username)
    print (item.user.id)
    print (item.created_time)
    print (item.id)

    recent_user = api.user(user_id=item.user.id)
    print (recent_user.counts['media'])
    print (recent_user.counts['followed_by'])
    print (recent_user.counts['follows'])

#location