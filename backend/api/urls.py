from django.urls import path
from . import views

urlpatterns = [
    path('storyline/start', views.get_story_background, name='storyline_background'),
    path('storyline/question', views.get_story_question, name='storyline_question'),
    path('storyline/choice', views.get_story_result_by_choice, name='storyline_choice'),
]