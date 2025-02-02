from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CardViewSet,
    DraftViewSet,
    DeckListViewSet,
    CubeUploadView,
    UpdateCardDatabaseView,
    DraftRoomView,
    popular_cubes_api,
    CubeDetailView

    
)
from a_drafting.views import PopularCubesView

router = DefaultRouter()
router.register(r'cards-list', CardViewSet)
router.register(r'decklist', DeckListViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path("upload-cube/", CubeUploadView.as_view(), name="cube-upload"),
    path('update-card-database/', UpdateCardDatabaseView.as_view(), name='update-card-database'),
    path('popular-cubes/', PopularCubesView.as_view(), name='popular_cubes'),
    path('api/popular-cubes/', popular_cubes_api, name='popular_cubes_api'),
    path('drafts/create-lobby/', DraftViewSet.as_view({'post': 'create_lobby'}), name='drafts-create-lobby'),
    path('drafting/<int:draft_id>/', DraftRoomView.as_view(), name='draft-lobby'),
    path('drafts/<int:pk>/start-draft/', DraftViewSet.as_view({'post': 'start_draft'}), name='start-draft'),
    path('cube/<int:pk>/', CubeDetailView.as_view(), name='cube_detail'),


]
