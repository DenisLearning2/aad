from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PostViewSet, GroupViewSet, CommentViewSet, FollowViewSet,
    CustomTokenRefreshView, CustomTokenVerifyView
)
from rest_framework_simplejwt.views import TokenObtainPairView

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'groups', GroupViewSet, basename='group')

urlpatterns = [
    path('', include(router.urls)),
    path('posts/<int:post_id>/comments/', CommentViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='comment-list'),
    path('posts/<int:post_id>/comments/<int:pk>/', CommentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='comment-detail'),
    path('follow/', FollowViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='follow-list'),
    path('follow/<int:pk>/', FollowViewSet.as_view({
        'delete': 'destroy'
    }), name='follow-detail'),
    path('jwt/create/', TokenObtainPairView.as_view(),
         name='token_obtain_pair'),
    path('jwt/refresh/', CustomTokenRefreshView.as_view(),
         name='token_refresh'),
    path('jwt/verify/', CustomTokenVerifyView.as_view(),
         name='token_verify'),
]
