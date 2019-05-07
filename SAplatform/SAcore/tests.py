from django.test import TestCase,RequestFactory
from .models import *
from .views import *
from rest_framework.test import APIRequestFactory
import json
from . import models

# Create your tests here.

def generateUser():
    u=User.objects.create(username="test",password="test",Type="U")
    
def generateAuthor():
    for i in range(1,10):
        u=User.objects.create(username="test%s"%(i),password="test%s"%(i),Type="E",telephone="123456")
        e=Author.objects.create(bind=u,name="Test Name%s"%(i))

def generateResource():
    generateAuthor()
    author=Author.objects.get(name="Test Name1")
    for i in range(1,20):
        r=Resource.objects.create(intro="test%s"%(i),title="test%s"%(i),url="testurl",owner=author)
        r.authors.add(author)   

def generateStarlist():        
    user=User.objects.get(username="test")
    for i in range(1,10):
        r=Resource.objects.get(pk=i)
        user.star_list.add(r)
        user.save()

def generateFollow():
    user=User.objects.get(username="test")
    for i in range(1,5):
        e=Author.objects.get(pk=i)
        user.followed_list.add(e)
        user.save()

def generateBuy():
    user=User.objects.get(username="test")
    for i in range(1,10):
        r=Resource.objects.get(pk=i)
        user.buyed_list.add(r)
        user.save()

def login_test_user():
    if not User.objects.filter(username="test"):
        generateUser()
    data={"username":"test","password":"test"}
    factory=APIRequestFactory()
    t_response=AuthView.as_view()(factory.post('login/',data,format='json'))
    token=json.loads(t_response.content)['token']
    return token

def login_test_author():
    generateAuthor()
    data={"username":"test1","password":"test1"}
    factory=APIRequestFactory()
    t_response=AuthView.as_view()(factory.post('login/',data,format='json'))
    token=json.loads(t_response.content)['token']
    return token


class TestRegisterView(TestCase):

    @classmethod
    def setUpTestData(cls):
        generateUser()
        cls.factory=APIRequestFactory()

    def test_register_exists(self):        
        data={"data":{"username":"test","password":"test"}}
        request=self.factory.post('register/',data, format='json')
        response=RegisterView.as_view()(request)
        self.assertContains(response,"msg",status_code=400)

    def test_register_noexists(self):
        data={"data":{"username":"test2","password":"test2","Type":"U","telephone":"test"}}
        request=self.factory.post('register/',data,format='json')
        response=RegisterView.as_view()(request)        
        self.assertEqual(response.status_code,200)

class TestAuthView(TestCase):
    @classmethod
    def setUpTestData(cls):
        generateUser()
        cls.factory=APIRequestFactory()

    def test_login_success(self):
        data={"username":"test","password":"test"}
        request=self.factory.post('login/',data,format='json')
        response=AuthView.as_view()(request)        
        self.assertEqual(json.loads(response.content)['code'],1000)      

    def test_login_wrpsw(self):
        data={"username":"test","password":"error"}
        request=self.factory.post('login/',data,format='json')
        response=AuthView.as_view()(request)       
        self.assertEqual(json.loads(response.content)['code'],1001)

    def test_login_no_user(self):
        data={"username":"test1","password":"error"}
        request=self.factory.post('login/',data,format='json')
        response=AuthView.as_view()(request)       
        self.assertEqual(json.loads(response.content)['code'],1001)

class TestProfileView(TestCase):
    @classmethod
    def setUpTestData(cls):        
        cls.factory=APIRequestFactory()
    
    def test_profile_get(self):        
        token=login_test_user()              
        d={'token':token}        
        request=self.factory.get('profile/',data=d)
        response=ProfileView.as_view()(request)        
        self.assertEqual(json.loads(response.content)['username'],'test')

    def test_profile_post(self):
        token=login_test_user()
        d={'data':{'username':'test','Type':'U','telephone':'123456'}}
        request=self.factory.post('profile/?token=%s'%(token),data=d,format='json')
        response=ProfileView.as_view()(request)              
        self.assertEqual(json.loads(response.content)['telephone'],'123456')

    def test_profile_put(self):
        token=login_test_user()
        d={'data':{'name':'test','instituition':'test','domain':'test'}}
        request=self.factory.put('profile/?token=%s'%(token),data=d,format='json')
        response=ProfileView.as_view()(request)
        self.assertEqual(json.loads(response.content)['msg'],"申请成功")

class TestAuthorView(TestCase):
    @classmethod
    def setUpTestData(cls):        
        cls.factory=APIRequestFactory()

    def test_author_get_success(self):
        token=login_test_author()
        d={'token':token}
        request=self.factory.get('au_profile/',data=d)
        response=AuthorView.as_view()(request)
        self.assertEqual(json.loads(response.content)['name'],'Test Name1')
    
    def test_author_get_fail(self):
        token=login_test_user()
        d={'token':token}
        request=self.factory.get('au_profile/',data=d)
        response=AuthorView.as_view()(request)
        self.assertContains(response,"msg",status_code=400)

    def test_author_post(self):
        token=login_test_author()
        data={'data':{'name':'New Test Name1','instituition':'BUAA'}}
        request=self.factory.post('au_profile/?token=%s'%(token),data=data,format='json')
        response=AuthorView.as_view()(request)
        self.assertEqual(json.loads(response.content)['name'],'New Test Name1')

class TestSearchView(TestCase):

    def test_search_get(self):
        token=login_test_user()
        generateResource()
        factory=APIRequestFactory()
        data={'token':token,'keyword':'test','page':1}
        request=factory.get('search/',data=data)
        response=SearchView.as_view()(request)
        self.assertEqual(len(json.loads(response.content)),10)

    def test_search_get_fail(self):
        token=login_test_user()
        generateResource()
        factory=APIRequestFactory()
        data={'token':token,'keyword':'fail'}
        request=factory.get('search/',data=data)
        response=SearchView.as_view()(request)
        self.assertEqual(json.loads(response.content),[])

class TestSearchDetailView(TestCase):
    @classmethod
    def setUpTestData(cls):
        generateResource()        

    def test_search_detail(self):
        token=login_test_user()
        factory=APIRequestFactory()
        data={'token':token,'id':'4'}
        request=factory.get('search_detail/',data=data)
        response=SearchDetailView.as_view()(request)
        self.assertEqual(json.loads(response.content)['authors'][0]['id'],1)

    def test_search_detail_noresource(self):
        token=login_test_user()
        factory=APIRequestFactory()
        data={'token':token,'id':'22'}
        request=factory.get('search_detail/',data=data)
        response=SearchDetailView.as_view()(request)
        self.assertContains(response,"msg",status_code=400)

    def test_search_detail_starred(self):        
        token=login_test_user()
        generateStarlist()
        factory=APIRequestFactory()
        data={'token':token,'id':'4'}
        request=factory.get('search_detail/',data=data)
        response=SearchDetailView.as_view()(request)
        self.assertEqual(json.loads(response.content)['starred'],True)

#用户收藏已经收藏过的文章会成功
class TestStarView(TestCase):
    @classmethod
    def setUpTestData(cls):
        generateUser()
        generateResource()
        generateStarlist()

    def test_star_get(self):
        token=login_test_user()
        factory=APIRequestFactory()
        data={'token':token}
        request=factory.get('star/',data=data)
        response=StarView.as_view()(request)
        self.assertEqual(len(json.loads(response.content)),9)

    def test_star_post(self):
        token=login_test_user()
        factory=APIRequestFactory()
        l=[]
        for i in range(10,16):
            l.append(i)
        data={'item_list':l}
        d={'data':data}
        request=factory.post('star/?token=%s'%(token),data=d,format='json')
        response=StarView.as_view()(request)
        self.assertEqual(json.loads(response.content)['msg'],"添加成功")

    def test_star_post_fail(self):
        token=login_test_user()
        factory=APIRequestFactory()
        l=[]
        for i in range(10,16):
            l.append(i)
        l.append(33)
        data={'item_list':l}
        d={'data':data}
        request=factory.post('star/?token=%s'%(token),data=d,format='json')
        response=StarView.as_view()(request)
        self.assertEqual(response.status_code,400)

    def test_star_delete(self):
        token=login_test_user()
        factory=APIRequestFactory()
        l=[]
        for i in range(2,6):
            l.append(i)
        data={'item_list':l}
        d={'data':data}
        request=factory.delete('star/?token=%s'%(token),data=d,format='json')
        response=StarView.as_view()(request)
        self.assertEqual(json.loads(response.content)['msg'],"已取消收藏")

    def test_star_delete_fail(self):
        token=login_test_user()
        factory=APIRequestFactory()
        l=[12,13]
        data={'item_list':l}
        d={'data':data}
        request=factory.delete('star/?token=%s'%(token),data=d,format='json')
        response=StarView.as_view()(request)
        self.assertEqual(response.status_code,400)
#post里关注失败status没有设为400，且与Star同理关注已关注的人可成功
class TestFollowView(TestCase):
    @classmethod
    def setUpTestData(cls):
        generateUser()
        generateAuthor()
        generateFollow()

    def test_follow_get(self):
        token=login_test_user()
        factory=APIRequestFactory()
        data={'token':token}
        request=factory.get('follow/',data=data)
        response=FollowView.as_view()(request)
        self.assertEqual(len(json.loads(response.content)),4)

    def test_follow_post(self):
        token=login_test_user()
        factory=APIRequestFactory()
        l=[]
        for i in range(6,8):
            l.append(i)
        data={'au_list':l}
        d={'data':data}
        request=factory.post('follow/?token=%s'%(token),data=d,format='json')
        response=FollowView.as_view()(request)
        self.assertEqual(json.loads(response.content)['msg'],"关注成功")

    def test_follow_post_fail(self):
        token=login_test_user()
        factory=APIRequestFactory()
        l=[]
        for i in range(6,8):
            l.append(i)
        l.append(13)
        data={'au_list':l}
        d={'data':data}
        request=factory.post('follow/?token=%s'%(token),data=d,format='json')
        response=FollowView.as_view()(request)
        self.assertEqual(response.status_code,400)

    def test_follow_delete(self):
        token=login_test_user()
        factory=APIRequestFactory()
        l=[]
        for i in range(2,4):
            l.append(i)
        data={'au_list':l}
        d={'data':data}
        request=factory.delete('follow/?token=%s'%(token),data=d,format='json')
        response=FollowView.as_view()(request)
        self.assertEqual(json.loads(response.content)['msg'],"已取消关注")

    def test_follow_delete_fail(self):
        token=login_test_user()
        factory=APIRequestFactory()
        l=[7,8]        
        data={'au_list':l}
        d={'data':data}
        request=factory.delete('follow/?token=%s'%(token),data=d,format='json')
        response=FollowView.as_view()(request)
        self.assertEqual(response.status_code,400)
#已购买的资源仍可购买
class TestBuyView(TestCase):
    @classmethod
    def setUpTestData(cls):
        generateUser()
        generateResource()
        generateBuy()
        user=User.objects.get(username="test")
        user.balance=12
        user.save()
        for i in range(1,20):
            r=Resource.objects.get(pk=i)
            r.price=i
            r.save()

    def test_buy_get(self):
        token=login_test_user()        
        factory=APIRequestFactory()
        data={'token':token}
        request=factory.get('buy/',data=data)
        response=BuyedView.as_view()(request)
        self.assertEqual(len(json.loads(response.content)),9)

    def test_buy_post_rich(self):
        token=login_test_user()        
        d={'data':{'item_id':10}}
        factory=APIRequestFactory()
        request=factory.post('buy/?token=%s'%(token),data=d,format='json')
        response=BuyedView.as_view()(request)
        self.assertEqual(json.loads(response.content)['msg'],"交易成功")

    def test_buy_post_poor(self):
        token=login_test_user()        
        d={'data':{'item_id':13}}
        factory=APIRequestFactory()
        request=factory.post('buy/?token=%s'%(token),data=d,format='json')
        response=BuyedView.as_view()(request)
        self.assertEqual(json.loads(response.content)['msg'],"余额不足")

    def test_buy_post_fail(self):
        token=login_test_user()        
        d={'data':{'item_id':23}}
        factory=APIRequestFactory()
        request=factory.post('buy/?token=%s'%(token),data=d,format='json')
        response=BuyedView.as_view()(request)
        self.assertEqual(json.loads(response.content)['msg'],"资源不存在")
