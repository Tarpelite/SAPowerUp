from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from .. import models

class Authentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.GET.get('token')
        # 检查用户的 token 是否合法
        token_obj = models.UserToken.objects.filter(token=token).first()
        if not token_obj:
                # rest_framework 会在内部捕捉这个异常并返回给用户认证失败的信息
                raise exceptions.AuthenticationFailed('用户认证失败')
        # 在 rest_framework 内部会将这两个字段赋值给request以供后续调用
        return (token_obj.user, token_obj)