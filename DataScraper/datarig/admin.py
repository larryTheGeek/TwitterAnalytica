from django.contrib import admin
from .models import ProfileAnalysisB, ProfileAnalysisT, TimelineAnalysis, SentimentAnalysis

# Register your models here.
admin.site.register(ProfileAnalysisB)
admin.site.register(ProfileAnalysisT)
admin.site.register(TimelineAnalysis)
admin.site.register(SentimentAnalysis)
