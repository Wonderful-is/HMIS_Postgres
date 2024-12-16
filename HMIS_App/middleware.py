# middleware.py
class UserSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'user_id' in request.session:
            request.user_id = request.session['user_id']
            request.username = request.session['username']
        response = self.get_response(request)
        return response