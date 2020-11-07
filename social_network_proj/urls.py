"""social_network_proj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf.urls import include, url
from rest_framework_jwt.views import obtain_jwt_token, refresh_jwt_token, verify_jwt_token
from rest_framework_swagger.views import get_swagger_view
from social_network.views import UserSignUp, AnalyticsListAPIView, ObtainJWTView

schema_view = get_swagger_view(title='Social Network API')

urlpatterns = [
    url(r'^api/token-auth/', obtain_jwt_token),
    url(r'^api/login/', view=ObtainJWTView.as_view(), name='login'),
    url(r'^api/token-refresh/', refresh_jwt_token),
    url(r'^api/token-verify/', verify_jwt_token),
    url(r'^api/sign-up/', UserSignUp.as_view()),
    url(r'^api/analytics/', AnalyticsListAPIView.as_view()),
    url(r'^api/', include('social_network.views')),
    url(r'^$', schema_view)
]
