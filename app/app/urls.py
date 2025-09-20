from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('lead/', include('lead.urls', namespace='lead'))
]
urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += [
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path(
            'schema/swagger/',
            SpectacularSwaggerView.as_view(url_name='schema'),
            name='swagger'
        ),
        path(
            'schema/redoc/',
            SpectacularRedocView.as_view(url_name='schema'),
            name='redoc'
        )
    ]
