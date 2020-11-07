from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework_jwt.serializers import JSONWebTokenSerializer, jwt_payload_handler, jwt_encode_handler
from django.contrib.auth import authenticate, user_logged_in

from social_network.models import UserProfile, Post, PostLike


class SignUpSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True,
                                     validators=[UniqueValidator(queryset=UserProfile.objects.all())])
    email = serializers.EmailField(required=True,
                                   validators=[UniqueValidator(queryset=UserProfile.objects.all())])
    password = serializers.CharField(required=True,
                                     max_length=50)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError('Passwords are not the same')
        return data

    class Meta:
        model = UserProfile
        fields = ('username', 'email', 'password', 'confirm_password')


class JWTSerializer(JSONWebTokenSerializer):
    def validate(self, attrs):
        credentials = {
            self.username_field: attrs.get(self.username_field),
            'password': attrs.get('password')
        }

        if all(credentials.values()):
            user = authenticate(request=self.context['request'], **credentials)

            if user:
                if not user.is_active:
                    msg = 'User account is disabled.'
                    raise serializers.ValidationError(msg)

                payload = jwt_payload_handler(user)
                user_logged_in.send(sender=user.__class__, request=self.context['request'], user=user)

                return {
                    'token': jwt_encode_handler(payload),
                    'user': user
                }
            else:
                msg = 'Unable to log in with provided credentials.'
                raise serializers.ValidationError(msg)
        else:
            msg = 'Must include "{username_field}" and "password".'
            msg = msg.format(username_field=self.username_field)
            raise serializers.ValidationError(msg)


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = ('id', 'username', 'email', 'phone', 'first_name', 'last_name', 'interests',
                  'about_me', 'city', 'country')


class UserActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = ('last_activity_datetime', 'last_request_datetime')


class PostSerializer(serializers.ModelSerializer):

    class Meta:
        model = Post
        fields = '__all__'


class LikesAnalyticsSerializer(serializers.ModelSerializer):
    created_count = serializers.ReadOnlyField()

    class Meta:
        model = PostLike
        fields = ('like_datetime', 'id', 'created_count')
