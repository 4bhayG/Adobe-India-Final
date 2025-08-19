from django.views.generic import TemplateView
from django.contrib import admin
from django.urls import path , include  ,re_path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('' , include('backend.urls')) ,
    path('api/' , include('backend.urls')) , 
    # re_path(r'^,*$'  , TemplateView.as_view(template_name = 'index.html'))
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, WhiteNoise will handle static files, but you might need nginx for media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
