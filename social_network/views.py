from django.db.models import Count
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework import routers
from rest_framework_jwt.views import ObtainJSONWebToken

from social_network.models import UserProfile, Post, PostLike
from social_network.serializers import SignUpSerializer, UserProfileSerializer, PostSerializer, UserActivitySerializer, \
    LikesAnalyticsSerializer, JWTSerializer
from social_network.permissions import UserIsOwner


class UserSignUp(GenericAPIView):
    serializer_class = SignUpSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.data.pop('confirm_password')
        user_info = request.data
        model_serializer = UserProfileSerializer(data=user_info)
        model_serializer.is_valid(raise_exception=True)
        UserProfile.objects.create_user(**user_info)
        return Response(model_serializer.data)


class ObtainJWTView(ObtainJSONWebToken):
    serializer_class = JWTSerializer


class UserViewSet(ModelViewSet):
    serializer_class = UserProfileSerializer
    queryset = UserProfile.objects.all()
    permission_classes = (IsAuthenticated, UserIsOwner)


class UserActivityViewSet(ModelViewSet):
    serializer_class = UserActivitySerializer
    queryset = UserProfile.objects.all()
    permission_classes = (IsAuthenticated, UserIsOwner)


class PostViewSet(ModelViewSet):
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        request.data.update({'user': request.user.id})
        return super(PostViewSet, self).create(request, *args, **kwargs)

    @action(detail=True, methods=['GET'])
    def like_unlike(self, request, *args, **kwargs):
        post_id = kwargs.pop('pk')
        user = request.user

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({
                'message': 'No such post',
                'ok': False
            })
        else:
            like_in_db = self._check_if_posts_already_liked(post, user)
            if like_in_db:
                like_in_db.delete()
                msg = f'Post was successfully unliked'
            else:
                PostLike.objects.create(post=post, user=user)
                msg = 'Post was successfully liked'
            return Response({
                'message': msg,
                'ok': True
            })

    @staticmethod
    def _check_if_posts_already_liked(post, user):
        liked_in_db = PostLike.objects.filter(post=post, user=user)
        if liked_in_db:
            return liked_in_db[0]
        return None


class AnalyticsListAPIView(ListAPIView):
    serializer_class = LikesAnalyticsSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        start_date = self.request.query_params.get('date_from', None)
        end_date = self.request.query_params.get('date_to', None)

        if not start_date or not end_date:
            raise Exception('Missed required params')

        return PostLike.objects.filter(like_datetime__range=[start_date, end_date])\
            .extra({'like_datetime': "date(like_datetime)"}).values('like_datetime').annotate(created_count=Count('id'))


router = routers.DefaultRouter()
router.register(r'post', PostViewSet)
router.register(r'user', UserViewSet)
router.register(r'user-activity', UserActivityViewSet)
urlpatterns = router.urls
