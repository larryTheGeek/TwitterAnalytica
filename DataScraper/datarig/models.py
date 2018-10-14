from django.db import models


#stores analysed data
class ProfileAnalysisB(models.Model):
    title = models.CharField(max_length=200)
    profile_stats_bar = models.ImageField(upload_to='Profile')
    

    def __str__(self):
        return self.title

class ProfileAnalysisT(models.Model):
    title = models.CharField(max_length=200)
    profile_stats_table = models.ImageField(upload_to='table')
    def __str__(self):
        return self.title

class TimelineAnalysis(models.Model):
    title = models.CharField(max_length=200)
    timeline_bar = models.ImageField(upload_to='bar')
    def __str__(self):
        return self.title

class SentimentAnalysis(models.Model):
    title = models.CharField(max_length=200)
    sentiment_pie = models.ImageField(upload_to='pie')
    def __str__(self):
        return self.title