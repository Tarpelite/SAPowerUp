from django.test import TestCase,RequestFactory
from .models import *
from .views import *
from rest_framework.test import APIRequestFactory
import json

# Create your tests here.

def generateUser():
    u=User.objects.create(username="test",password="test")
    return u

class TestRegister(TestCase):

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

