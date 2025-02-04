from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentUploadViewSet, QueryView

router = DefaultRouter()
router.register(r'documents', DocumentUploadViewSet, basename='document')

urlpatterns = [
    path('api/', include(router.urls)),
    path('upload/', DocumentUploadViewSet.as_view({'post': 'create'}), name='upload'),
    path('query/', QueryView.as_view(), name='query'),
]
