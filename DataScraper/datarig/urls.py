from django.urls import path
from . import views

urlpatterns = [
    path('',views.index, name='index' ),
    path('profile', views.profile_data_analysis, name='profile'),
    path('base', views.base, name='base' ),
    path('analysis', views.analysis_display, name='display'),
    path('count', views.timeline_analysis, name='timeline'),
    path('timeline', views.timeline_display, name='timeline_display'),
    path('sentiment', views.sentiment_analysis, name='sentiment'),
    path('sen-data', views.sentiment_display, name='sentiment_display')

]