import orm
from models import User, Blog, Comment
import asyncio
import sys

async def test(loop):
    await orm.create_pool(loop, user='www-data', password='www-data', db='blog')
    u1 = User(name='Test1', email='test1@test.com', passwd='123456', image='about:blank')
    await u1.save()
    u2 = User(name='Test2', email='test2@test.com', passwd='7890', image='about:blank')
    await u2.save()

loop = asyncio.get_event_loop()
loop.run_until_complete(test(loop))
loop.close()
if loop.is_closed():
    sys.exit(0)
