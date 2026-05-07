from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from posapp.forms import POSAuthenticationForm


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=POSAuthenticationForm,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("posapp.urls")),
    path("api/", include("posapp.api_urls")),
]
