import json
import os
import datetime
import re
import math
import time
import pandas as pd
import matplotlib.pyplot as plt
from pandas.tools.plotting import table
from io import BytesIO
import folium
import tweepy

#word analysis tools
import string
from collections import Counter
from nltk.tokenize import TweetTokenizer
from nltk.corpus import stopwords
from textblob import TextBlob

    
#django specific tools
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .client import create_twitter_client
from .forms import ProfileNameForm ,TimeLineNameForm, SentimentForm
from tweepy import Stream, StreamListener, Cursor
from .models import ProfileAnalysisB,ProfileAnalysisT, TimelineAnalysis, SentimentAnalysis


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
my_path = os.path.abspath(__file__)
def index(request):
    """contains the path to the home page"""

    return render(request, 'home.html')

def base(request):
    return render(request, 'base.html')

def profile_data_analysis(request):
    dirpath = os.getcwd()
    """This view scrapes data from twitter and stores it to the Db """
    if request.method == 'POST':
        form = ProfileNameForm(request.POST)
        if form.is_valid():
            profile = form.cleaned_data['Profile_name']
            #set the profile as a session variable to be used later
            request.session['profile'] = profile
            
            client = create_twitter_client()
            user = client.get_user(profile)
            data = vars(user)

            #remove objects from data
            mydict = { k:v for k,v in data.items() if k!='_api' and (isinstance(v , datetime.date)!= True)}
            
           
            def paginate(items, n):
                for i in range(0, len(items), n):
                    yield items[i:i+n]
        
            #gets timeline data and stores it into a jsonl file
            fname = 'user_timeline_{}.jsonl'.format(profile)
            with open(os.path.join(dirpath, fname), 'w') as f:
                for page in Cursor(client.user_timeline, screen_name=profile, counter=200).pages(16):
                    for status in page:
                        f.write(json.dumps(status._json) + "\n")


            #get profile data
            fname = "profile_{}.json".format(profile)
            with open(os.path.join(dirpath, fname), 'w') as f:
                for page in Cursor(client.home_timeline, count=200).pages(4):
                    for status in page:
                        f.write(json.dumps(status._json) + "\n")

            #read profile data
        
            
            followers = mydict['followers_count']
            tweets = mydict['statuses_count']

           #read timeline data
            timeline_file = 'user_timeline_{}.jsonl'.format(profile)
            with open(timeline_file) as f:
                favorited_count, retweet_count = [], []
                for line in f:
                    tweet = json.loads(line)
                    favorited_count.append(tweet['favorite_count'])
                    retweet_count.append(tweet['retweet_count'])
            
            avg_favorite = round(sum(favorited_count)/tweets, 2)
            avg_retweet  = round(sum(retweet_count)/tweets, 2)
            
            #sample data analysis
            x = ['followers', 'no of favorites', 'retweets']
            y = [followers, round(sum(favorited_count)), sum(retweet_count)]

            #plot bar for the sample data
            x_count = [x for x in range(len(x))]
            plt.bar(x_count, y)
            plt.xticks(x_count, x , rotation= 30)
            plt.title('profile statistics')
            plt.ylabel("count")
            plt.tight_layout()
            f = BytesIO()
            plt.savefig(f)
            content_file = ContentFile(f.getvalue())

            
            
    
            labels = ['followers', 'tweets', 'favorite', 'retweets', 'average favourite', 'average retweet']
            counts = [followers, tweets, round(sum(favorited_count)), round(sum(retweet_count)), avg_favorite, avg_retweet]
            
            df = pd.DataFrame()
            df['profile statistics'] = labels
            df['counts'] = counts
            df = df.set_index('profile statistics')
            df.columns.name = df.index.name
            df.index.name = None
            
            #plot a dataframe with profile stats
            fig, ax = plt.subplots(figsize=(15,5))
            ax.xaxis.set_visible(False)
            ax.yaxis.set_visible(False)
            ax.set_frame_on(False)
            tabla = table(ax, df, loc='upper right', colWidths=[0.23]*len(df.columns))
            tabla.auto_set_font_size(False)
            tabla.set_fontsize(16)
            tabla.scale(2.2,2.2)
            f = BytesIO()
            plt.savefig(f)
            content_file = ContentFile(f.getvalue())
            profile_dataT = ProfileAnalysisT()
            profile_dataT.title = profile
            profile_dataT.profile_stats_table.save('{}_table.png'.format(profile), content_file)
            profile_dataT.save()

            return redirect('display')

            #plt.savefig('stats.png', transparent=True
    else:
        form = ProfileNameForm()

    return render(request, 'profile.html', {'form':form})

def analysis_display(request):
    profile =  request.session['profile']
    analysis = ProfileAnalysisT.objects.filter(title=profile)
    n=len([analysis])
    analysis = analysis[n-1]
    return render(request, 'analysis.html', {'analysis': analysis})

def timeline_analysis(request):
    dirpath = os.getcwd()
    if request.method == 'POST':
        form = TimeLineNameForm(request.POST)
        #gets form data if its valid
        if form.is_valid():
            profile = form.cleaned_data['timeline_name']
            request.session['profile'] = profile
            

            #creates a twitter API client 
            client = create_twitter_client()
            
            #scrapes data and stores it to a jsonl file
            fname = '{}.jsonl'.format(profile)
            with open(os.path.join(dirpath, fname), 'w') as f:
                for page in Cursor(client.user_timeline, screen_name=profile,counter=200).pages(16):
                    for status in page:
                        f.write(json.dumps(status._json) + "\n")

            
            def process(text, tokenizer=TweetTokenizer(), stopwords=[]):
                """Process the text of a tweet ie.
                -lowercase
                -Tokenize
                -stopword removal 

                returns a list of strings
                """
                text = text.lower()
                tokens = tokenizer.tokenize(text)
                return [tok for tok in tokens if tok not in stopwords and not tok.isdigit()]
            
            def load_data(file):
                tweet_tokenizer = TweetTokenizer()
                punct = list(string.punctuation)
                stopword_list = stopwords.words('english')+punct+['rt','via', '...','…', '’', '️']
                
                #???
                tf = Counter()
                #sample data
                text = []
                created_at = []
                lan = []

                #loads data from a json file
                with open(file, 'r') as f:
                    for line in f:
                        tweet = json.loads(line)
                        text.append(tweet['text'])
                        created_at.append(tweet['created_at'])
                        lan.append(tweet['lang'])

                sample = pd.DataFrame({'created_at':created_at, 'text': text, 'language':lan})
                output = sample.set_index('created_at')
                output.columns.name = output.index.name
                output.index.name = None
                new_output = output.head(10)

                #read from a csv file
                with open(file, 'r') as f:
                    for line in f:
                        tweet = json.loads(line)
                        #gets the words token
                        tokens = process(text=tweet['text'], tokenizer=tweet_tokenizer, stopwords=stopword_list)
                        tf.update(tokens) 
                #values for plotting
                y = [count for tag, count in tf.most_common(5)]
                x = [tag for tag, count in tf.most_common(5)]

                p1 = [count for tag, count in tf.most_common(10)]
                p2 = [tag for tag, count in tf.most_common(10)]
                
                #create a dataframe object and make word the index
                word_count_dataframe= pd.DataFrame({'COUNT':p1, 'WORD':p2})
                df = word_count_dataframe.set_index('WORD')
                df.columns.name = df.index.name
                df.index.name = None
                 
                #graph plot
                x_count = [x for x in range(len(p2))]
                plt.bar(x_count, p1)   

                plt.xticks(x_count, p2, rotation= 30)
                plt.title("Term frequencies")
                plt.ylabel("frequency")
                plt.xlabel('Terms') 
                plt.tight_layout() 
                f = BytesIO()
                plt.savefig(f)
                content_file = ContentFile(f.getvalue())
                timeline_data = TimelineAnalysis()
                timeline_data.title= profile
                timeline_data.timeline_bar.save('{}_bar.png'.format(profile), content_file)
                timeline_data.save()
                   
            load_data(fname)
            return redirect('timeline_display')

    else:
        form = TimeLineNameForm()
    return render(request, 'timeline_analysis.html', {'form':form})
    
def timeline_display(request):
    profile =  request.session['profile']
    timeline = TimelineAnalysis.objects.filter(title=profile)
    n=len(timeline)
    timeline = timeline[n-1]
    return render(request, 'timeline.html', {'timeline': timeline})       


def sentiment_analysis(request):
    
    class TwitterClient():
        """generic twitter class for sentiment analysis"""
        def __init__(self):
            self.api = create_twitter_client()

        def clean_tweet(self, tweet):
            '''
            utility function to clean tweets by removing links, special characters
            using simple regex statements.
            '''
            return ''.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)", "",tweet).split())
            
        def get_tweet_sentiment(self, tweet):
            '''
            Utility function to classify sentiment of passed tweet
            using textblob's sentiment method.
            '''
            # create TextBlob object of passed tweet text
            analysis = TextBlob(self.clean_tweet(tweet))
            #set sentiment
            if analysis.sentiment.polarity > 0:
                return 'positive'
            elif analysis.sentiment.polarity == 0:
                return 'neutral'

            else:
                return 'negative'


        def get_tweets(self, query, count=10):
            '''
            Main function to fetch tweets and parse them
            '''
            # empty list to store parsed tweets
            tweets = []

            try:
                # call twitter api to fetch tweets
                fetched_tweets = self.api.search(q=query, count = count)

                #parsing tweets one by one
                for tweet in fetched_tweets:
                    # empty dictionary to store required params of a tweet
                    parsed_tweet = {}

                    # saving text of tweet
                    parsed_tweet['text'] = tweet.text
                    # saving sentiment of tweet
                    parsed_tweet['sentiment'] = self.get_tweet_sentiment(tweet.text)

                    # appending parsed tweet to tweets list
                    if tweet.retweet_count > 0:
                        # if tweet has retweets ensure it is appended only once
                        if parsed_tweet not in tweets:
                            tweets.append(parsed_tweet)
                    else:
                        tweets.append(parsed_tweet)

                return tweets

            except tweepy.TweepError as e:
                print("Error:" + str(e))
    if request.method == 'POST':
        form = SentimentForm(request.POST)
        #gets form data if its valid
        if form.is_valid():
            #model database model object
            sentiment = SentimentAnalysis()
            tag = form.cleaned_data['sentiment_name']
            request.session['tag'] = tag

            sentiment.title = tag
            
            api = TwitterClient()
            # calling function to get tweets
            tweets = api.get_tweets(query=tag, count=200)
            
            # picking postive tweets from tweets
            ptweets = [tweet for tweet in tweets if tweet['sentiment']== 'positive']
            ntweets = [tweet for tweet in tweets if tweet['sentiment'] == 'negative']
            neutral = [tweet for tweet in tweets if tweet['sentiment'] == 'neutral']
            labels = 'Positive', 'Negative', 'neutral'
            sizes = [len(ptweets), len(ntweets), len(neutral)]
            colors = ['green', 'yellow','red']

            
            

            


            plt.pie(sizes,  labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)

            plt.axis('equal')
            f = BytesIO()
            plt.savefig(f)
            content_file = ContentFile(f.getvalue())
            sentiment.sentiment_pie.save('{}_pie.png'.format(tag), content_file)
            sentiment.save()
            return redirect('sentiment_display')
    else:
        form = SentimentForm()
    return render(request, 'sentiment_analysis.html', {'form':form})
    
def sentiment_display(request):
    tag =  request.session['tag']
    
    sentiment = SentimentAnalysis.objects.filter(title=tag)
    sentiment = sentiment[0]
    return render(request, 'sentiment.html', {'sentiment': sentiment, })       
