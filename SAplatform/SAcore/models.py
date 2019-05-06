from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import timedelta

# Create your models here.
class User(AbstractUser):
    '''
    用户类
    '''
    TYPE_CHOICES = (
        ('U', 'User'),
        ('E', 'Expert'),
    )
    telephone = models.CharField(max_length=20)
    Type = models.CharField(max_length=1, choices = TYPE_CHOICES)
    avator = models.ImageField(upload_to="SAcore/static/user_avator", blank=True)
    balance = models.IntegerField(default=0)
    star_list = models.ManyToManyField('Resource', blank=True, related_name="star_list")
    buyed_list = models.ManyToManyField('Resource', blank=True, related_name="buyed_list")
    followed_list = models.ManyToManyField('Author', blank=True)

    def __str__(self):
        return self.username

class UserToken(models.Model):
    user = models.OneToOneField(to="User", on_delete=models.CASCADE)
    token = models.CharField(max_length=64)

    def __str__(self):
        return self.user.username

class Author(models.Model):
    '''
    专家，只有绑定用户才会成为专家用户
    '''

    name = models.CharField(max_length=255, unique=True)
    instituition = models.CharField(max_length=255, blank=True)
    domain = models.CharField(max_length=255, blank=True)
    bind = models.OneToOneField(User, on_delete=models.CASCADE, blank=True)
    citation_num = models.IntegerField(default=0, blank=True)
    article_num = models.IntegerField(default=0, blank=True)
    coworkers = models.ManyToManyField("self", blank=True)
    resources = models.ManyToManyField('Resource', blank=True)
    h_index = models.IntegerField(default=0, blank=True)
    g_index = models.IntegerField(default=0, blank=True)
    avator = models.ImageField(upload_to="SAcore/static/author_avator", blank=True)

    def __str__(self):
        return self.name


class Resource(models.Model):
    '''
    资源类
    '''

    TYPE_CHOICES = (
        ("P1", "Paper"),
        ("P2", "Patent"),
        ("P3", "Project"),
    )

    title = models.CharField(max_length=255, unique=True)
    authors = models.ManyToManyField(Author, blank=True)
    intro = models.TextField(blank=True)
    url = models.TextField(blank=True)
    price = models.IntegerField(default=0)
    Type = models.CharField(max_length=2, choices=TYPE_CHOICES)
    publisher = models.CharField(max_length=255, blank=True)
    publish_date = models.CharField(max_length=255, blank=True)
    citation_nums = models.IntegerField(default=0, blank=True)
    agency = models.CharField(max_length=255, blank=True)
    patent_number = models.TextField(blank=True)
    patent_applicant_number = models.TextField(blank=True)
    file = models.FileField(upload_to="SAcore/static/files", blank=True)
    owner = models.ForeignKey('Author', blank=True, related_name='owner', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

class U2E_apply(models.Model):
    '''
    普通用户申请成为专家的申请表
    '''

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_created=True)
    name = models.CharField(max_length=255, default=" ")
    instituition = models.CharField(max_length=255, blank=True)
    domain = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.user.username + " : " + self.name

    def approve(self):
        try:
            au1 = Author.objects.get(name = self.name)
        except Author.DoesNotExist:
            au1 = Author.objects.create(name = self.name)
        au1.institutition = self.instituition
        au1.domain = self.domain
        au1.bind = self.User
        try:
            au1.save()
            self.delete()
            return True
        except Exception as e:
            print(e)
            return False
    


class publish_apply(models.Model):
    '''
    专家用户申请发布资源的申请表
    '''

    TYPE_CHOICES = (
        ("P1", "Paper"),
        ("P2", "Patent"),
        ("P3", "Project"),
    )

    au = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="applicant")
    title = models.CharField(max_length=255)
    authors = models.ManyToManyField(Author, blank=True, related_name="authors")
    intro = models.TextField()
    url = models.TextField(blank=True)
    price = models.IntegerField(default=0)
    Type = models.CharField(max_length=2, choices=TYPE_CHOICES)
    created_time = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="SAcore/static/files", blank=True)

    def __str__(self):
        return self.au.name + " : " + self.title
    
    def approve(self):
        try:
            r1 = Resource.object.create(
                title = self.title,
                intro = self.intro,
                url = self.url,
                price = self.price,
                Type = self.Type,
                file = self.file,
                owner = self.au
            )
            for aut in authors:
                r1.authors.add(aut)
                aut.resources.add(r1)
            r1.save()
            self.delete()
            return True
        except Exception as e:
            print(e)
            return False

class Bidding(models.Model):

    '''
    竞价记录
    '''

    au = models.ForeignKey(Author, on_delete = models.CASCADE)
    price = models.IntegerField(default=0)

    def __str__(self):
        return self.au.name + " -- " + str(self.price) 

class Auction(models.Model):

    '''
    转让资源发起竞拍
    '''

    start_au = models.ForeignKey(Author, related_name="start_au", on_delete=models.CASCADE)
    participants = models.ManyToManyField(Author, related_name="participants")
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    started_time = models.DateTimeField(auto_now_add=True)
    period = models.IntegerField(default=3600) #以秒为单位记录持续时间
    price = models.IntegerField(default=0)
    candidate = models.ForeignKey(Author, related_name="candidate", on_delete=models.CASCADE)

    def __str__(self):
        return self.resource.title 



        


    
