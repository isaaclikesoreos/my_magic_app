from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomUserViewSet,
    CubeViewSet,
    CardViewSet,
    DraftViewSet,
    DeckListViewSet,
    CurrentUserView,
    CubeUploadView,
    UpdateCardDatabaseView
)

router = DefaultRouter()
router.register(r'users', CustomUserViewSet)
router.register(r'cubes-list', CubeViewSet)
router.register(r'cards-list', CardViewSet)
router.register(r'drafts', DraftViewSet)
router.register(r'decklist', DeckListViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('cubes/upload/', CubeUploadView.as_view(), name='cube-upload'),
    path('current-user/', CurrentUserView.as_view(), name='current-user'),
    path('cards/update/', UpdateCardDatabaseView.as_view(), name='update-card-database'),
    # Explicitly add the create_lobby endpoint
    path('drafts/create-lobby/', DraftViewSet.as_view({'post': 'create_lobby'}), name='create-lobby'),
]
