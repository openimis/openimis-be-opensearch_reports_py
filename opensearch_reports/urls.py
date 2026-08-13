from django.urls import path

from opensearch_reports import views

urlpatterns = [
    path("auth_check", views.opensearch_auth_check),
]
