from django.urls import path
from . import views


urlpatterns = [
    path('', views.home),
    path('upload_documents/' , view= views.uploadPdf , name = 'upload-pdfs'),
    path("find_relevant_sections/" , view = views.Get_Relevant_Topics , name = "Get_base_logic") ,
    path("get_insights/" , view = views.generate_insights , name = "Generate_Insights" ),
    path("generate_audio_podcast/" , view = views.podcast , name = "Podcast_generation")
]
