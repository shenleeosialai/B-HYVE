from django.urls import path

from . import views

app_name = 'images'

urlpatterns = [
    path('create/', views.image_create, name='create'),
    path('detail/<int:id>/<slug:slug>/', views.image_detail, name='detail'),
    path('like/', views.image_like, name='like'),
    path('comment/', views.image_comment, name='comment'),
    path('', views.image_list, name='list'),
    path('ajax/delete/', views.ajax_delete_image, name='ajax_delete_image'),
    path('ranking/', views.image_ranking, name='ranking'),
    # path('', views.story_list, name='story_list'),
    path('story/<int:story_id>/', views.story_detail, name='story_detail'),
    path('delete-story-image/', views.delete_story_image,
         name='delete_story_image'),
    path('log-story-view/', views.log_story_view, name='log_story_view'),
    path('story-viewers/', views.story_viewers, name='story_viewers'),

]
