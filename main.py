import json
import tweepy
import ConfigParser
import urllib2
from urllib import urlencode
from time import sleep

# creating config object
config = ConfigParser.RawConfigParser()
config.read('config.cfg')

# getting twitter properties 
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

# Getting the application properties
SLEEP_TIME = config.get('Application', 'SLEEP_TIME')
REVISION_TRACKER_FILENAME = config.get('Application', 'REVISION_TRACKER_FILENAME')

def run():
	''' The main program function.
	'''
	response = urllib2.urlopen('http://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles=Kosovo&rvlimit=5&rvprop=timestamp|ids|user|comment&format=json')
	json_response = json.load(response)

	# Get the title. 17391 is the id of the 'Kosovo' article.
	# FIXME: Don't rely on hardcoded value (i.e. 17391).
	title = json_response['query']['pages']['17391']['title']

	# Get the revisions. 17391 is the id of the 'Kosovo' article.
	# FIXME: Don't rely on hardcoded value (i.e. 17391).
	revisions = json_response['query']['pages']['17391']['revisions']

	# For now, we will only check the latest revision.
	# We'll make the polling occur at a high enough frequency that will minimize the risks of missing a revision.
	#
	# TODO: Check older revisions as well to make sure we didn't miss any: this will happen if more than one
	# revision is submitted between two requests to Wikipedia's API.
	latest_revision = revisions[0]

	# Only process this revision if we haven't done so already in our last request.
	# In other words, let's not attempt to make duplicate tweets.
	if is_new_revision(latest_revision):

		# Build revision url. e.g. http://en.wikipedia.org/w/index.php?title=Kosovo&diff=619399922&oldid=619329366
		url = build_wikipedia_revision_url(title, latest_revision)

		# Requesting bitly shortened url of revision url
		shortened_url = shorten_url(url)

		# building the twitter message 
		user = latest_revision['user']
		twitter_message = "%s edited the '%s' article: %s" % (user, title, shortened_url) 

		print twitter_message

		# tweet message
		api.update_status(twitter_message)

		# Store the current revision number as the previous revision number.
		# We do this to check if the next revision we will pull won't be the same one as this one. 
		# In other words, we will want to check if no new edits were made since the last request.
		# If no new edits were made since the last request, then we won't tweet anything.
		store_latest_revision_id(latest_revision)

def build_wikipedia_revision_url(article_title, revision):
	''' Build the wikipedia revision diff URL.
	:param article_title: The title of the article.
	:param revision: The revision.
	'''
	rev_id = revision['revid']
	parent_id = revision['parentid']
	user = revision['user']

	url = "http://en.wikipedia.org/w/index.php?title=%s&diff=%d&oldid=%d" % (article_title, rev_id, parent_id)

	return url

def shorten_url(url):
	''' Uses Bitly API to shorten a given url.
	:param url: The url to shorten.
	'''

	# Make the request to the API.
	params = urlencode({'longUrl': url, 'login':BITLY_USERNAME, 'apiKey':BITLY_API_KEY, 'format': 'json'})
	req = urllib2.Request("http://api.bit.ly/v3/shorten?%s" % params)

	# Process the response.
	response_bitly = urllib2.urlopen(req)
	response_bitly_json = json.load(response_bitly)

	shortened_url = response_bitly_json['data']['url']

	return shortened_url

def is_new_revision(revision):
	''' Checks if the given revision is a new one.
	:param revision: The revision object.
	'''
	current_revision_id = revision['revid']

	with open(REVISION_TRACKER_FILENAME, "r") as revision_tracking_file:
		previous_revision_id = revision_tracking_file.read()

	# Check if current and previous revision are the same
	current_revision_is_a_new_revision = int(current_revision_id) != int(previous_revision_id)

	return current_revision_is_a_new_revision

def store_latest_revision_id(revision):
	''' Store the last revision number.
	:param revision: The lastest revision.
	'''
	
	#TODO: We will eventually have to handle multiple revisions when we'll want to monitor more than one article.
	
	# Get revision id.
	latest_revision_id = revision['revid']

	# Store it in a file.
	with open(REVISION_TRACKER_FILENAME, "w") as revision_tracking_file:
		revision_tracking_file.write(str(latest_revision_id))


# Infinite application loop, commence!
while True:
	run()

	# Wait for a bit before checking if there are any new edits.
	# But not too much that we would risk missing an edits (because we only look at the latest edit for now)
	sleep(10)

