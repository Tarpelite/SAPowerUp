from django.urls import path
from django.conf.urls import url, re_path
from SAcore import views

urlpatterns = [
    path('login/', views.AuthView.as_view()),
    path('profile/', views.ProfileView.as_view()),
    path('au_profile/', views.AuthorView.as_view()),
    path('register/', views.RegisterView.as_view()),
    path('search/', views.SearchView.as_view()),
    path('search_detail/', views.SearchDetailView.as_view()),
    path('star_detail/', views.StarDetailView.as_view()),
    path('follow/', views.FollowView.as_view()),
    path('buy/', views.BuyedView.as_view()),
]
