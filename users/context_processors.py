def user_email_processor(request):
    if request.user.is_authenticated:
        return {'current_user_email': request.user.email}
    return {}
