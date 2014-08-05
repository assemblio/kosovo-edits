from urllib import urlencode
import urllib2
import json
import tweepy, time, sys
import ConfigParser

# creating config object
config = ConfigParser.RawConfigParser()
config.read('config.cfg')

# get twitter properties 
TWITTER_CONSUMER_KEY = config.get('Twitter', 'CONSUMER_KEY')
TWITTER_CONSUMER_SECRET = config.get('Twitter', 'CONSUMER_SECRET')
TWITTER_ACCESS_KEY = config.get('Twitter', 'ACCESS_KEY')
TWITTER_ACCESS_SECRET = config.get('Twitter', 'ACCESS_SECRET')

# creating twitter api object 
auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET)
api = tweepy.API(auth)

# getting bitly properties
BITLY_USERNAME = config.get('Bitly', 'USERNAME')
BITLY_API_KEY = config.get('Bitly', 'API_KEY')


 
response = urllib2.urlopen('http://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles=Kosovo&rvlimit=5&rvprop=timestamp|ids|user|comment&format=json')
json_response = json.load(response)
title = json_response['query']['pages']['17391']['title']

revisions = json_response['query']['pages']['17391']['revisions']


for revision in revisions:
	#build revision url. e.g. http://en.wikipedia.org/w/index.php?title=Kosovo&diff=619399922&oldid=619329366
	rev_id = revision['revid']
	parent_id = revision['parentid']
	user = revision['user']

	url = "http://en.wikipedia.org/w/index.php?title=%s&diff=%d&oldid=%d" % (title, rev_id, parent_id)
	
	# requesting bitly shortened url of revision url
	params = urlencode({'longUrl': url, 'login':BITLY_USERNAME, 'apiKey':BITLY_API_KEY, 'format': 'json'})
	req = urllib2.Request("http://api.bit.ly/v3/shorten?%s" % params)
	response_bitly = urllib2.urlopen(req)
	response_bitly_json = json.load(response_bitly)
	shortened_url = response_bitly_json['data']['url']

	# building the twitter message 
	twitter_message = "%s edited the '%s' article: %s" % (user, title, shortened_url) 
	print twitter_message 
	
	# tweet message
	
	



