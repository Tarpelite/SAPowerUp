from django.shortcuts import render
from SAcore.models import *
from SAcore.Se import *
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework import exceptions
from SAcore.utils.auth import Authentication
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination

# Create your views here.

def md5(user):
        import hashlib
        import time

        ctime = str(time.time())

        m = hashlib.md5(bytes(user, encoding='utf-8'))
        m.update(bytes(ctime, encoding='utf-8'))
        return m.hexdigest()

class AuthView(APIView):
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        ret = {
            'code':1000,
            'msg':None
        }
        try:
            user = request.data.get('username')
            pwd = request.data.get('password')
            obj = User.objects.filter(username=user, password=pwd).first()
            if not obj:
                ret['code'] = 1001
                ret['msg'] = '用户名或密码错误'
            
            token = md5(user)
            UserToken.objects.update_or_create(user=obj, defaults={'token':token})
            ret['token'] = token
        
        except Exception as e:
            print(e)
            ret['code'] = 1002
            ret['msg'] = '请求异常'

        return JsonResponse(ret)


class ProfileView(APIView):
    '''
        个人信息相关业务
    '''
    authentication_classes = [Authentication,]

    #获得个人信息
    def get(self, request, *args, **kwargs):

        token = request.data['token']
        user = UserToken.objects.filter(token = token).first().user
        user_se = UserSerializer(user)
        return JsonResponse(user_se.data)

    #修改个人信息
    def post(self, request, *args, **kwargs):
        
        token = request.data['token']
        user = UserToken.objects.filter(token = token).first().user
        data = request.data['data']
        user_se = UserSerializer(user, data=data)
        if user_se.is_valid():
            user_se.save()
            return JsonResponse(user_se.data)
        return JsonResponse(user_se.errors, status=400)

    #申请成为专家
    def put(self, request, *args, **kwargs):

        token = request.data['token']
        user = UserToken.objects.filter(token = token).first().user
        if not user:
            return JsonResponse({'msg':'用户认证失败'}, status=400)
        data = request.data['data']
        try:
            U2E_apply.objects.create(
                user = user,
                created_time = timezone.now(),
                name = data['name'],
                instituition = data['instituition'],
                domain = data['domain']
            )
            return JsonResponse({'msg':"申请成功"})
        except Exception as e:
            return JsonResponse({'msg':"申请失败"}, status=404)
    

class AuthorView(APIView):
    '''
    专家信息相关业务
    '''
    #用户认证
    authentication_classes = [Authentication,]

    #获得专家个人信息
    def get(self, request, *args, **kwargs):
        token = request.data['token']
        user = UserToken.objects.filter(token = token).first().user
        if user.Type == 'U':
            return JsonResponse({'msg':"该用户为普通用户，请先升级为专家用户"}, status=400)
        au = Author.objects.filter(bind=user).first()
        au_se = AuthorSerializer(au)
        return JsonResponse(au_se.data, status=200)
    
    #修改专家个人信息
    def post(self, request, *args, **kwargs):
        token = request.data['token']
        data = request.data['data']
        user = UserToken.objects.filter(token = token).first().user
        if user.Type == 'U':
            return JsonResponse({'msg':"该用户为普通用户，请先升级为专家用户"}, status=400) 
        au = Author.objects.filter(bind=user).first()
        au_se = AuthorSerializer(au, data = data)
        if au_se.is_valid():
            au_se.save()
            return JsonResponse(au_se.data)
        return JsonResponse(au_se.errors, status = 400)
    

class RegisterView(APIView):
    '''
    注册视图
    '''
    authentication_classes = []
    def post(self, request, *args, **kwargs):
        data = request.data['data']
        username = data['username']
        user = User.objects.filter(username=username).first()
        if user:
            return JsonResponse({'msg':"该用户名已被注册， 换一个试试吧"}, status=400)
        user_se = RegisterSerializer(data = data)
        if user_se.is_valid():
            user_se.save()
            return JsonResponse(user_se.data, status=200)
        return JsonResponse(user_se.errors, status=400)


class SearchView(APIView):
    '''
    搜索视图
    '''
    authentication_classes = [Authentication,]
    def get(self, request, *args, **kwargs):
        token = request.data['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        data = request.data['data']
        keyword = data['keyword']
        result = Resource.objects.filter(title__contains=keyword).order_by("id")
        pg = PageNumberPagination()
        page_result = pg.paginate_queryset(queryset=result, request=request, view=self)
        result_se = ResourceSerializer(instance=page_result, many=True)
        return JsonResponse(result_se.data, safe=False)


class SearchDetailView(APIView):
    '''
        展示某一条搜索结果的详细信息
    '''
    authentication_classes = [Authentication,]

    def get(self, request, *args, **kwargs):
        ret = {}
        token = request.data['token']
        ret['token'] = token
        data = request.data['data']
        item_id = data['id']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        try:
            r1 = Resource.objects.get(pk=item_id)
            authors = []
            for au in r1.authors.all():
                record = {
                    'id':au.id,
                    'name':au.name
                }
                authors.append(record)
            ret['authors'] = authors
        except Exception as e:
            return JsonResponse({'msg':"该资源不存在"}, status=400)
        
        r1 = user.star_list.filter(pk=item_id).first()
        if r1:
            ret['starred'] = True
        else:
            ret['starred'] = False
        return JsonResponse(ret)
        

class StarView(APIView):
    '''
    收藏视图
    '''
    authentication_classes = [Authentication,]
    
    #列出当前用户的所有收藏
    def get(self, request, *args, **kwargs):
        token = request.data['token']
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        res = user.star_list.all()
        pg = PageNumberPagination()
        page_result = pg.paginate_queryset(queryset=res, request=request, view=self)
        result_se = ResourceSerializer(isinstance=page_result, many=True)
        return JsonResponse(result_se.data)

    #批量添加收藏
    def post(self, request, *args, **kwargs):
        token = request.data['token']
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        data = request.data['data']
        star_items = data['item_list']
        for i in star_items:
            try:
                r1 = Resource.objects.get(pk=i)
                user.star_list.add(r1)
                user.save()
            except Exception as e:
                return JsonResponse({"msg":"添加收藏失败"}, status=400)
        
        return JsonResponse({"msg":"添加成功"}, status=200)
    
    #批量取消收藏
    def delete(self, request, *args, **kwargs):
        token = request.data['token']
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        data = request.data['data']
        star_items = data['item_list']
        for i in star_items:
            try:
                r1 = user.star_list.get(pk=i)
                user.star_list.remove(r1)
                user.save()
            except Exception as e:
                return JsonResponse({"msg":"取消收藏失败"}, status=400)
        return JsonResponse({"msg":"已取消收藏"}, status = 200)

        
class StarDetailView(APIView):
    '''
        收藏夹资源细节
    '''
    authentication_classes = [Authentication,]

    #获得某一条资源的作者信息
    def get(self, request, *args, **kwargs):
        ret = {}
        token = request.data['token']
        ret['token'] = token
        data = request.data['data']
        item_id = data['id']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        try:
            r1 = Resource.objects.get(pk=item_id)
            authors = []
            for au in r1.authors.all():
                record = {
                    'id':au.id,
                    'name':au.name
                }
                authors.append(record)
            ret['authors'] = authors
        except Exception as e:
            return JsonResponse({'msg':"该资源不存在"}, status=400)
        return JsonResponse(ret)


class FollowView(APIView):
    '''
        关注视图
    '''

    authentication_classes = [Authentication,]
    
    #列出所有关注的专家
    def get(self, request, *args, **kwargs):
        token = request.data['token']
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        res = user.follow_list.all()
        pg = PageNumberPagination()
        page_result = pg.paginate_queryset(queryset=res, request=request, view=self)
        result_se = AuthorSerializer(isinstance=page_result, many=True)
        return JsonResponse(result_se.data)
    
    #批量添加关注
    def post(self, request, *args, **kwargs):
        token = request.data['token']
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        data = request.data['data']
        follow_aus = data['au_list']
        for i in follow_aus:
            try:
                au = Author.objects.get(pk=i)
                user.follow_list.add(au)
                User.save()
            except Exception as e:
                return JsonResponse({"msg":"添加关注失败"})
        return JsonResponse({"msg":"关注成功"},status=200)
    
    #批量取消关注
    def delete(self, request, *args, **kwargs):
        token = request.data['token']
        if not token:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        data = request.data['data']
        follow_aus = data['au_list']
        for i in follow_aus:
            try:
                au = user.follow_list.get(pk=i)
                user.follow_list.remove(au)
                user.save()
            except Exception as e:
                return JsonResponse({"msg":"取消关注失败"}, status = 400)
        return JsonResponse({"msg":"已取消关注"})


class BuyedView(APIView):
    '''
        已购资源视图
    '''
    #用户认证
    authentication_classes = [Authentication,]
    #列出所有已购资源
    def get(self, request, *args, **kwargs):
        token = request.data['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        result = user.buyed_list.all()
        pg = PageNumberPagination()
        page_result = pg.paginate_queryset(queryset=result, request=request, view=self)
        result_se = ResourceSerializer(instance=page_result, many=True)
        return JsonResponse(result_se.data, safe=False)
    
    #购买资源
    def post(self, request, *args, **kwargs):
        token = request.data['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        data = request.data['data']
        item_id = data['item_id']
        try:
            r1 = Resource.objects.get(pk=item_id)
        except Resource.DoesNotExist:
            return JsonResponse({"msg":"资源不存在"}, status=404)
        
        if user.balance < r1.price:
            return JsonResponse({'msg':"余额不足"}, status=400)
        try:
            user.balance -= r1.price
            user.buyed_list.add(r1)
            user.save()
        except Exception as e:
            return JsonResponse({'msg':"交易失败"}, status=400)
        return JsonResponse({"msg":"交易成功", "balance":user.balance})


class ResourceView(APIView):
    '''
        展示某一资源
    '''
    #用户认证
    authentication_classes = [Authentication,]
    
    #获取资源文件或者url
    def get(self, request, *args, **kwargs):
        token = request.data['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        flag = False
        data = request.data['data']
        item_id = data['item_id']
        url = ""
        try:
            r1 = Resource.objects.get(pk=item_id)
        except Exception as e:
            return JsonResponse({'msg':'请求资源不存在'},status = 400)
        if r1.price == 0:
            flag = True
        elif user.Type == 'E':
            au = Author.objects.filter(bind=user).first()
            if au:
                resource = au.resources.filter(pk=r1.id).first()
                if resource:
                    flag = True
                    url = resource.url
                else:
                    flag = False
        elif user.Type == 'U':
            resource = user.buyed_list.filter(pk=r1.pk).first()
            if resource:
                flag = True
                url = resource.url
            else:
                flag = False
        
        ret = {
            'token':token,
            'data':{
                'flag':flag,
                'url':url
            }
        }
        return JsonResponse(ret)



    








    



        





        



