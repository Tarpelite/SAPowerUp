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
from rest_framework.parsers import FileUploadParser, MultiPartParser
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore,register_events, register_job
import datetime
# Create your views here.

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")
scheduler.start()

def md5(user):
        import hashlib
        import time

        ctime = str(time.time())

        m = hashlib.md5(bytes(user, encoding='utf-8'))
        m.update(bytes(ctime, encoding='utf-8'))
        return m.hexdigest()

def finish_auction(auc_id):
    auc = Auction.objects.filter(id=auc_id).first()
    try:
        start_au = auc.start_au
        resource = auc.resource
        candidate = auc.candidate
        price = auc.price
        if not candidate:
            Message.objects.create(
                text = "无人出价，资源流拍" + resouce.title,
                created_time = timezone.now(),
                to_user = start_au
            )
            return False
        if price > candidate.bind.balance:
            Message.objects.create(
                text = "拍卖结束，但你的余额不足，无法拍到"+resource.title,
                created_time = timezone.now(),
                to_user = candidate.bind
            )
            return False
        else:
            candidate.bind.balance -= price
            candidate.resources.add(resource)
            resource.owner = candidate
            start_au.resources.remove(resource)
            start_au.bind.balance += price
            auc.delete()
            candidate.save()
            candidate.bind.save()
            resource.save()
            start_au.bind.save()
            start_au.save()
        Message.objects.create(
            text = resource.title +  "\n拍卖结束，你已成功拍到该商品",
            created_time = timezone.now(),
            to_user = candidate.bind
        )
        return True
    except Exception as e:
        print(e)
        Message.objects.create(
            text = resource.title +  " 拍卖异常, 已取消",
            created_time = timezone.now(),
            to_user = candidate.bind
        )
        Message.objects.create(
            text = resource.title +  " 拍卖异常, 已取消",
            created_time = timezone.now(),
            to_user = start_au.bind,
        )
        return False
    return True
    

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
            else:   #测试发现的错误，没有else对于密码错误情况一样会执行下方代码
                token = md5(user)
                UserToken.objects.update_or_create(user=obj, defaults={'token':token})
                ret['token'] = token
                ret['type'] = obj.Type
        
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

        token = request.GET['token']
        user = UserToken.objects.filter(token = token).first().user
        user_se = UserSerializer(user)
        return JsonResponse(user_se.data)

    #修改个人信息
    def post(self, request, *args, **kwargs):
        
        token = request.GET['token']
        user = UserToken.objects.filter(token = token).first().user
        data = request.data['data']
        user_se = UserSerializer(user, data=data)
        if user_se.is_valid():
            user_se.save()
            return JsonResponse(user_se.data)
        return JsonResponse(user_se.errors, status=400)

    #申请成为专家
    def put(self, request, *args, **kwargs):

        token = request.GET['token']
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

    #文件parser
    parser_classes = (MultiPartParser,)
    #获得专家个人信息
    def get(self, request, *args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token = token).first().user
        if user.Type == 'U':
            return JsonResponse({'msg':"该用户为普通用户，请先升级为专家用户"}, status=400)
        au = Author.objects.filter(bind=user).first()
        au_se = AuthorSerializer(au)
        return JsonResponse(au_se.data, status=200)
    
    #修改专家个人信息
    def post(self, request, *args, **kwargs):
        token = request.GET['token']
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
    
    #发布资源
    def put(self, request, *args, **kwargs):
        token = request.GET['token']
        data = request.data
        print(data)
        attach_file = request.FILES['file']
        user = UserToken.objects.filter(token = token).first().user
        if user.Type == 'U':
            return JsonResponse({'msg':"该用户为普通用户，请先升级为专家用户"}, status=400) 
        au = Author.objects.filter(bind=user).first()
        if not au:
            return JsonResponse({'msg':"该用户尚未绑定专家用户"}, status=400)
        try: 
            apply = publish_apply.objects.create(
                au = au,
                title = data['title'],
                intro = data['intro'],
                url = data['url'],
                price = data['price'],
                Type = data['Type'],
                created_time = timezone.now()
            )
        except Exception as e:
            print(e)
            return JsonResponse({'msg':"创建申请失败"}, status=400)
        if attach_file:
            apply.file.save(attach_file.name, attach_file, save=True)
        authors_text = data['authors']
        authors_names = authors_text.split(',')
        for name in authors_names:
            try:
                au_ = Author.objects.get(name=name)
            except Author.DoesNotExist:
                au_ = Author.objects.create(name = name)
            apply.authors.add(au_)
        apply.save()
        return JsonResponse({'msg':"创建成功"})
            
        
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
    #用户认证
    authentication_classes = [Authentication,]

    #获取搜索结果
    def get(self, request, *args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        keyword = request.GET['keyword']
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
        token = request.GET['token']
        ret['token'] = token
        item_id = request.GET['id']
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
        token = request.GET['token']
        user = UserToken.objects.filter(token = token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        res = user.star_list.all().order_by("id")
        pg = PageNumberPagination()
        page_result = pg.paginate_queryset(queryset=res, request=request, view=self)
        result_se = ResourceSerializer(instance=page_result, many=True)
        return JsonResponse(result_se.data, safe=False)

    #批量添加收藏
    def post(self, request, *args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token = token).first().user
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
        token = request.GET['token']
        user = UserToken.objects.filter(token = token).first().user
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
        token = request.GET['token']
        ret['token'] = token
        item_id = request.GET['id']
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
        buyed_r = user.buyed_list.filter(pk=r1.id).first()
        if buyed_r:
            ret['buyed'] = True
        else:
            ret['buyed'] = False
        return JsonResponse(ret)


class FollowView(APIView):
    '''
        关注视图
    '''

    authentication_classes = [Authentication,]
    
    #列出所有关注的专家
    def get(self, request, *args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token = token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        res = user.followed_list.all()
        pg = PageNumberPagination()
        page_result = pg.paginate_queryset(queryset=res, request=request, view=self)
        result_se = AuthorSerializer(instance=page_result, many=True)
        return JsonResponse(result_se.data, safe=False)
    
    #批量添加关注
    def post(self, request, *args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token = token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        data = request.data['data']
        follow_aus = data['au_list']
        for i in follow_aus:
            try:
                au = Author.objects.get(pk=i)
                user.followed_list.add(au)
                user.save()
            except Exception as e:
                print(e)
                return JsonResponse({"msg":"添加关注失败"},status=400)
        return JsonResponse({"msg":"关注成功"},status=200)
    
    #批量取消关注
    def delete(self, request, *args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token = token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        data = request.data['data']
        follow_aus = data['au_list']
        for i in follow_aus:
            try:
                au = user.followed_list.get(pk=i)
                user.followed_list.remove(au)
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
        token = request.GET['token']
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
        token = request.GET['token']
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
        token = request.GET['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        flag = False
        item_id = request.GET['item_id']
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
                'url':url
            }
        }
        return JsonResponse(ret)


class AvatorView(APIView):
    '''
        头像相关业务
    '''

    #验证身份
    authentication_classes = [Authentication,]

    #获取头像
    def get(self, request, *args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        if user.Type == 'U':
            ret = {
                'url':user.avator.name.split('/')[-1]
            }
            return JsonResponse(ret)
        elif user.Type == 'E':
            au = Author.objects.filter(bind=user).first()
            if not au:
                return JsonResponse({'msg':'未找到对应专家用户，请确认身份'}, status=400)
            ret = {
                'url':au.avator.name.split('/')[-1]
            }
            return JsonResponse(ret)
    
    #上传头像
    def post(self, request, *args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        image = request.FILES['image']
        if user.Type == 'U':
            se = UserAvatorSerializer(user, data={'avator':image})
            if se.is_valid():
                se.save()
                return JsonResponse(se.data)
            return JsonResponse(se.errors, status=400)
        elif user.Type == 'E':
            au = Author.objects.filter(bind=user).first()
            if not au:
                 return JsonResponse({'msg':'未找到对应专家用户，请确认身份'}, status=400)
            se = AuthorAvatorSerializer(au, data={'avator':image})
            if se.is_valid():
                se.save()
                return JsonResponse(se.data)
            return JsonResponse(se.errors, status=400)
        

class CoworkerView(APIView):
    '''
        关系图相关业务
    '''

    #验证身份
    authentication_classes = [Authentication,]

    #获取关系矩阵
    def get(self, request, *args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        au = Author.objects.filter(bind=user).first()
        if not au:
            return JsonResponse({'msg':"该用户不是专家用户"}, status=400)
        user = au
        nodes = []
        edges = []
        query_set = user.coworkers.all()
        for n1 in query_set :
            name = n1.name
            if name not in nodes:
                nodes.append(name)
            edges.append(
                {
                    'source':user.name,
                    'target':n1.name,
                    'weight':1,
                    'name':'coworker'
                }
            )
            n2_query_set = n1.coworkers.all()
            for n2 in n2_query_set:
                if n2.name in nodes:
                    edges.append(
                {
                    'source':user.name,
                    'target':n1.name,
                    'weight':1,
                    'name':'coworker'
                }
            )
                else:
                    continue
        names = [
            {"name":x} for x in nodes
        ]
        names.append(
            {"name":user.name,
            "symbol":"star"}
        )
        ret = {
            "nodes":names,
            "links":edges
        }
        return JsonResponse(ret)


class AuctionView(APIView):
    '''
        转让资源（以拍卖形式）
    '''

    #用户认证
    authentication_classes = [Authentication,]

    #获取当前转让列表(未完成)
    def get(self, request, *args, **kwargs):

        token = request.GET['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        au  = Author.objects.filter(bind=user).first()
        if not au:
            return JsonResponse({'msg':"不是专家用户，无法查看拍卖"}, status=400)
        res = Auction.objects.all()
        pg = PageNumberPagination()
        page_result = pg.paginate_queryset(queryset=res, request=request, view=self)
        result_se = ResourceSerializer(instance=page_result, many=True)
        return JsonResponse(result_se.data, safe=False)

    #发起转让
    def post(self, request, *args, **kwargs):
        token = request.GET['token']
        data = request.data['data']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        au  = Author.objects.filter(bind=user).first()
        if not au:
            return JsonResponse({'msg':"不是专家用户，无法发起拍卖"}, status=400)
        r_id = data['resource_id']
        r1 = Resource.objects.filter(id=r_id).first()
        if not r1:
            return JsonResponse({'msg':"该资源不存在"}, status=400)
        if r1.owner.id != au.id:
            return JsonResponse({'msg':"没有权限拍卖资源"}, status=400)
        try:
            auc = Auction.objects.create(
                start_au = au,
                resource = r1,
                started_time = datetime.datetime.strptime(data['start_time'], "%Y-%m-%d %H:%M:%S"),
                period = data['period'],
                price = data['price']
            )
            auc.save()
            finished_time = auc.started_time + timedelta(seconds=data['period'])
            scheduler.add_job(finish_auction, 'cron', id=str(auc.id), year=finished_time.year, month=finished_time.month, day = finished_time.day, misfire_grace_time=30, hour= finished_time.hour, minute=finished_time.minute, second=finished_time.second,args=[auc.id])
            register_events(scheduler)
        except Exception as e:
            print(e)
            scheduler.shutdown()
        except Exception as e:
            return JsonResponse({'msg':str(e)}, status=400)
        return JsonResponse({"msg":"发起拍卖成功"}, status = 200)

    # 出价
    def put(self, request,*args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        au  = Author.objects.filter(bind=user).first()
        if not au:
            return JsonResponse({'msg':"不是专家用户，无法查看拍卖"}, status=400)
        
        data = request.data
        auc_id = data['id']
        price = data['price']
        auc = Auction.objects.filter(pk=auc_id).first()
        if not auc:
            return JsonResponse({"msg":"该拍卖不存在"}, status=400)
        if price > auc.price:
            auc.price = price
            auc.candidate = au
            auc.save()
            return JsonResponse({'msg':"出价成功， 目前的价格是 "+str(price)})
    
    # 取消转让
    def delete(self, request,*args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        au  = Author.objects.filter(bind=user).first()
        if not au:
            return JsonResponse({'msg':"不是专家用户，无法查看拍卖"}, status=400)
        data = request.data
        auc_id = request.data["id"]
        auc = Auction.objects.filter(pk=auc_id).first()
        if not auc:
            return JsonResponse({'msg':'该拍卖不存在'},status=400)
        if auc.resource.owner.id != au.id:
            return JsonResponse({'msg': '没有权限'}, status=400)
        try:
            auc.delete()
            return JsonResponse({'msg':"拍卖已取消"})
        except Exception as e:
            print(e)
            return JsonResponse({'msg':"无法取消"}, status=400)
    
  
class RechargeView(APIView):
    '''
        充值视图
    '''
    #用户认证
    authentication_classes = [Authentication,]

    # 充值
    def post(sefl, request, *args, **kwargs):
        token = request.GET['token']
        user = UserToken.objects.filter(token=token).first().user
        if not user:
            return JsonResponse({'msg':"用户认证已失效，请重新登录"}, status=400)
        key = request.data['key']
        card = RechargeCard.objects.filter(token=key).first()
        if not card:
            return JsonResponse({'msg':"无效的充值卡"}, status = 400)
        try:
            user.balance +=card.amout
            card.delete()
        except Exception as e:
            return JsonResponse({'msg':"充值失败"}, status=400)
        return JsonResponse({'msg':"充值成功"}, status=200)
    
        















    








    



        





        



