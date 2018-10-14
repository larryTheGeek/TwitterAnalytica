from django import forms

class ProfileNameForm(forms.Form):
    Profile_name = forms.CharField(widget=forms.TextInput(
                      attrs={
                          'class': 'prof'
                      }
    ))


class TimeLineNameForm(forms.Form):
    timeline_name = forms.CharField(widget=forms.TextInput(
                      attrs={
                          'class': 'prof'
                      }
    ))

class SentimentForm(forms.Form):
    sentiment_name = forms.CharField(widget=forms.TextInput(
                      attrs={
                          'class': 'prof'
                      }
    ))
