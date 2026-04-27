from rest_framework import serializers
from posts.models import Post, Group, Comment, Follow
from rest_framework.relations import SlugRelatedField
from rest_framework_simplejwt.serializers import (
    TokenRefreshSerializer, TokenVerifySerializer)
from rest_framework.exceptions import AuthenticationFailed


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except AuthenticationFailed:
            raise serializers.ValidationError(
                {"detail": "Token is invalid or expired",
                 "code": "token_not_valid"}
            )


class CustomTokenVerifySerializer(TokenVerifySerializer):
    def validate(self, attrs):
        try:
            return super().validate(attrs)
        except AuthenticationFailed:
            raise serializers.ValidationError(
                {"detail": "Token is invalid or expired",
                 "code": "token_not_valid"}
            )


class PostSerializer(serializers.ModelSerializer):
    author = SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        fields = '__all__'
        model = Post


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    post = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ('id', 'author', 'text', 'created', 'post')

    def create(self, validated_data):
        # post будет передан из вьюхи через context или напрямую
        request = self.context.get('request')
        post_id = self.context.get('post_id')
        if post_id:
            post = Post.objects.get(id=post_id)
            validated_data['post'] = post
            validated_data['author'] = request.user
        return super().create(validated_data)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'title', 'slug', 'description')


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    following = serializers.CharField(source='following.username',
                                      read_only=True)

    class Meta:
        model = Follow
        fields = ('user', 'following')

    def validate_following(self, value):
        request = self.context.get('request')
        if request and request.user == value:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя!")
        return value
