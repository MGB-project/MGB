def profile_context(request):
    if request.user.is_authenticated:
        return {"profile": request.user}  # Передаём user напрямую
    return {}
