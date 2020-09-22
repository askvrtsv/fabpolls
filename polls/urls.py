from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from polls import views

urlpatterns = [
    path('polls/', views.PollList.as_view()),
    path('polls/<int:pk>/', views.PollDetail.as_view()),
    path('polls/<int:pk>/publish/', views.poll_publish_view),
    path('polls/<int:pk>/pass/', views.poll_pass_view),
    path('polls/<int:pk>/results/', views.poll_results_view),
    path('questions/', views.QuestionList.as_view()),
    path('questions/<int:pk>/', views.QuestionDetail.as_view()),
    path('answerchoices/', views.AnswerChoiceList.as_view()),
    path('answerchoices/<int:pk>/', views.AnswerChoiceDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
