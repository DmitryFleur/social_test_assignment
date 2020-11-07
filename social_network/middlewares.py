from django.utils import timezone


class UserAnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user_profile = request.user

        if user_profile.is_authenticated:
            user_profile.last_request_datetime = timezone.now()
            user_profile.save()

        return response
