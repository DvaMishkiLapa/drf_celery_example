from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('lead/', include('lead.urls', namespace='lead')),
]

if settings.DEBUG:
    custom_prefix = ''
    urlpatterns += [
        path(f'{custom_prefix}schema/', SpectacularAPIView.as_view(), name='schema'),
        path(
            f'{custom_prefix}schema/swagger/',
            SpectacularSwaggerView.as_view(url_name='schema'),
            name='swagger',
        ),
        path(
            f'{custom_prefix}schema/redoc/',
            SpectacularRedocView.as_view(url_name='schema'),
            name='redoc',
        ),
    ]
