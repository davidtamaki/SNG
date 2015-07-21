import requests
from requests_oauthlib import OAuth1
from flask import Markup

# import twitter keys and tokens
from config import *

class TwitterOEmbedder(object):

    def __init__(self, app=None, cache=None, debug=None):
        if app and cache:
            self.init(app, cache, debug)

    def init(self, app, cache, timeout=None, debug=None):
        twitter_timeout = 60*60*24*365
        max_timeout = {'saslmemcached':60*60*24*30,
                       'simple': twitter_timeout}

        if not timeout:
            default_timeout = app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
            timeout = min(max_timeout['saslmemcached'],twitter_timeout)

        if timeout > twitter_timeout:
            raise Exception("TwitterOEmbedder: Cache expiry should not exceed 1 year "
                            "per Twitter API specification")


        @app.context_processor
        def tweet_processor():
            def oembed_tweet(tweet_id,
                             access_token=twitter_access_token,
                             token_secret=access_token_secret,
                             omit_script=False):
                auth = OAuth1(consumer_key,
                              consumer_secret,
                              access_token,
                              token_secret)
                url = 'https://api.twitter.com/1.1/statuses/oembed.json'

                @cache.memoize(timeout=timeout)
                def get_tweet_html(tweet_id, omit_script):
                    params = {'id':tweet_id,
                              'omit_script':omit_script}
                    r = requests.get(url, params=params, auth=auth)

                    try:
                        tweet_html = Markup(r.json()[u'html'])
                    except KeyError as e:
                        if debug or (debug is None and app.debug):
                            raise e
                        else:
                            return ''
                    return tweet_html
                return get_tweet_html(tweet_id, omit_script)
            return dict(oembed_tweet=oembed_tweet)
