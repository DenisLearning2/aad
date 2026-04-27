from rest_framework import viewsets, permissions, status
from rest_framework.pagination import LimitOffsetPagination
from django.shortcuts import get_object_or_404
from posts.models import Post, Group, Comment, Follow, User
from .serializers import (
    PostSerializer, GroupSerializer,
    CommentSerializer,
    CustomTokenRefreshSerializer, CustomTokenVerifySerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView


class CustomTokenRefreshView(TokenRefreshView):
    serializer_class = CustomTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except InvalidToken:
            return Response(
                {
                    "detail": "Token is invalid or expired",
                    "code": "token_not_valid"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception:
            return Response(
                {
                    "detail": "Token is invalid or expired",
                    "code": "token_not_valid"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CustomTokenVerifyView(TokenVerifyView):
    serializer_class = CustomTokenVerifySerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except InvalidToken:
            return Response(
                {
                    "detail": "Token is invalid or expired",
                    "code": "token_not_valid"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception:
            return Response(
                {
                    "detail": "Token is invalid or expired",
                    "code": "token_not_valid"
                },
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response({}, status=status.HTTP_200_OK)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            self.permission_denied(self.request, "Недостаточно прав")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """Удаление поста (только автор)"""
        instance = self.get_object()

        # Проверка авторизации
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Проверка: автор ли текущий пользователь
        if instance.author != request.user:
            return Response(
                {"detail":
                    "У вас недостаточно прав для "
                    "выполнения данного действия."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Удаляем пост
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):
        limit = request.query_params.get('limit')
        offset = request.query_params.get('offset')

        queryset = self.filter_queryset(self.get_queryset())

        # Если есть параметры пагинации - возвращаем пагинированный ответ
        if limit is not None or offset is not None:
            paginator = LimitOffsetPagination()
            page = paginator.paginate_queryset(queryset, request)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

        # Без параметров - просто массив
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    pagination_class = None
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='list')
    def group_list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='details')
    def group_details(self, request, pk=None):
        group = self.get_object()
        serializer = self.get_serializer(group)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = None

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        if post_id:
            return Comment.objects.filter(post_id=post_id)
        return Comment.objects.none()

    def get_object(self):
        post_id = self.kwargs.get('post_id')
        comment_id = self.kwargs.get('pk')
        return get_object_or_404(Comment, id=comment_id, post_id=post_id)

    def create(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)

        text = request.data.get('text', '').strip()

        if not text:
            return Response(
                {"text": ["Обязательное поле."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        comment = Comment.objects.create(
            author=request.user,
            post=post,
            text=text
        )

        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        comment = self.get_object()

        # Проверка прав: только автор может редактировать
        if comment.author != request.user:
            return Response(
                {"detail": "У вас недостаточно прав для "
                 "выполнения данного действия."},
                status=status.HTTP_403_FORBIDDEN
            )

        text = request.data.get('text', '').strip()

        if not text:
            return Response(
                {"text": ["Обязательное поле."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        comment.text = text
        comment.save()

        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        comment = self.get_object()

        # Проверка прав: только автор может редактировать
        if comment.author != request.user:
            return Response(
                {"detail": "У вас недостаточно прав для "
                 "выполнения данного действия."},
                status=status.HTTP_403_FORBIDDEN
            )

        if 'text' in request.data:
            text = request.data.get('text', '').strip()
            if not text:
                return Response(
                    {"text": ["Обязательное поле."]},
                    status=status.HTTP_400_BAD_REQUEST
                )
            comment.text = text
            comment.save()

        serializer = self.get_serializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        """Удаление комментария - ТОЛЬКО АВТОР"""
        comment = self.get_object()

        # Важно: проверка на superuser или staff отключена
        # Только автор комментария может его удалить
        if comment.author != request.user:
            return Response(
                {
                    "detail":
                        "У вас недостаточно прав для выполнения "
                        "данного действия."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    def list(self, request):
        """GET /api/v1/follow/"""
        follows = self.get_queryset()
        data = [
            {"user": f.user.username, "following": f.following.username}
            for f in follows
        ]
        return Response(data, status=status.HTTP_200_OK)

    def create(self, request):
        """POST /api/v1/follow/"""
        following_username = request.data.get('following')

        if not following_username:
            return Response(
                {"following": ["Обязательное поле."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            following_user = User.objects.get(username=following_username)
        except User.DoesNotExist:
            return Response(
                {
                    "following": [
                        f"Объект с username={following_username} "
                        "не существует."
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user == following_user:
            return Response(
                {"following": ["Нельзя подписаться на самого себя!"]},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Follow.objects.filter(user=request.user,
                                 following=following_user).exists():
            return Response(
                {"detail": "Вы уже подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        Follow.objects.create(user=request.user, following=following_user)

        return Response(
            {
                "user": request.user.username,
                "following": following_user.username
            },
            status=status.HTTP_201_CREATED
        )

    def destroy(self, request, pk=None):
        """DELETE /api/v1/follow/{id}/"""
        try:
            follow = self.get_queryset().get(id=pk)
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Follow.DoesNotExist:
            return Response(
                {"detail": "Страница не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )
