"""
URL configuration for the API endpoints related to the storyline feature.
Maps URL paths to their corresponding view functions.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('storyline/start', views.get_story_scenario, name='storyline_background'),
    path('storyline/question', views.get_story_question, name='storyline_question'),
    path('storyline/choice', views.get_story_result_by_choice, name='storyline_choice'),
    path('storyline/result', views.get_story_result, name='storyline_result'),

    path('storyline/state', views.get_story_state, name='storyline_state'),
    path('storyline/reset', views.reset_story, name='storyline_reset'),

    path('rag/retrieve', views.rag_retrieve, name='rag_retrieve'),
]