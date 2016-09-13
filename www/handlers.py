import re, time, json, logging, hashlib, base64, asyncio
from coroweb import get, post
from models import User, Comment, Blog, next_id

@get('/')
async def index(request):
    # day1
    # return web.Response(body=b'<h1>LOL</h1>')
    # day4
    users = await User.findAll()
    return {
        '__template__': 'test.html',
        'users': users
    }
