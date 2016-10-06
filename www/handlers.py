import re, time, json, logging, hashlib, base64, asyncio
from coroweb import get, post
from models import User, Comment, Blog, next_id
from apis import APIError, APIValueError, APIResourceNotFoundError
from aiohttp import web
import sys
sys.path.append("..")
from conf.config import configs

@get('/')
async def index(request):
    # day1
    # return web.Response(body=b'<h1>LOL</h1>')
    # day4
    # users = await User.findAll()
    summary = 'Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs = [
        Blog(id='1', name='Test Blog', summary=summary, created_at=time.time()-120),
        Blog(id='2', name='Something New', summary=summary, created_at=time.time()-3600),
        Blog(id='3', name='Learn Swift', summary=summary, created_at=time.time()-7200)
    ]
    return {
        '__template__': 'blogs.html',
        'blogs': blogs
    }

@get('/register')
def register():
    return {
        '__template__': 'register.html'
    }

@get('/signin')
def signin():
    return {
        '__template__': 'signin.html'
    }

@get('/signout')
def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user signed out.')
    return r

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')

COOKIE_NAME = 'blogsession'
_COOKIE_KEY = configs['session']['secret']

def user2cookie(user, max_age):
    '''
    Generate cookie str by user.
    '''
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

async def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L = cookie_str.split('-')
        if len(L) != 3:
            return None
        uid, expires, sha1 = L
        if int(expires) < time.time():
            return None
        user = await User.find(uid)
        if user is None:
            return None
        s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd = '******'
        return user
    except Exception as e:
        logging.exception(e)
        return None

@post('/api/users')
async def api_register_user(*, name, passwd, email):
    if not name or not name.strip():
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users_by_email = await User.findAll('email=?', [email])
    users_by_name = await User.findAll('name=?', [name])
    if len(users_by_email) > 0:
        raise APIError('register:failed', 'email', 'Email is already in use.')
    if len(users_by_name) > 0:
        raise APIError('register:failed', 'name', 'Name is already in use.')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid, passwd)
    user = User(id=uid, name=name.strip(), email=email, passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image='')
    await user.save()
    # make session cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@post('/api/finduser')
async def api_find_user(*, name='', email=''):
    user_by_name = user_by_email = []
    if name != '':
        user_by_name = await User.findAll('name=?', [name])
    if email != '':
        user_by_email = await User.findAll('email=?', [email])
    if len(user_by_name) > 0 or len(user_by_email) > 0:
        return web.Response(text="false")
    return web.Response(text="true")

@post('/api/authenticate')
async def authenticate(*, nameOrEmail, passwd):
    if not nameOrEmail:
        raise APIValueError('email', 'Invalid email.')
    if not passwd:
        raise APIValueError('passwd', 'Invalid password.')
    users = await User.findAll('name=?', [nameOrEmail])
    if len(users) == 0:
        users = await User.findAll('email=?', [nameOrEmail])
        if len(users) == 0:
            raise APIValueError('nameOrEmail', 'nameOrEmail not exit.')
    user = users[0]
    sha22 = '%s:%s' % (user.id, passwd)
    sha22_passwd = hashlib.sha1(sha22.encode('utf-8')).hexdigest()
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise APIValueError('passwd', 'Invalid password.')
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user,86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r
