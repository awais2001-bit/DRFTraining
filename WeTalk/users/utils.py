from rest_framework_simplejwt.tokens import RefreshToken

def set_jwt_cookies(response, refresh: RefreshToken):
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    response.set_cookie(
        key="access",
        value=access_token,
        httponly=True,
        secure=False,   # change to True in production (HTTPS only)
        samesite="Strict",
        max_age=3600
    )
    response.set_cookie(
        key="refresh",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="Strict",
        max_age=7*24*60*60
    )
    return response


def clear_jwt_cookies(response):
    response.delete_cookie("access")
    response.delete_cookie("refresh")
    return response
