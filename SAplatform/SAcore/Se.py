from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'Type', 'avator', 'balance', 'email', 'telephone')

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'Type', 'email', 'telephone')


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ('id', 'name', 'instituition', 'domain', 'citation_num', 'article_num', 'h_index', 'g_index', 'avator')

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ('id', 'title', 'intro', 'price', 'Type')

class UserAvatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('avator',)

class AuthorAvatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ('avator',)

        