#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author : yasin
# @time   : 11/20/18 7:30 PM
# @File   : main.py

import tornado.ioloop
import tornado.web
import tornado.httpclient
import tornado.httputil
import tornado.gen
import json
import redis

import config
from config import logger

wechatRedis = redis.Redis(host=config.redisIp, port=config.redisPort, db=0)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Welcome to use wechat access token server!")


class TokenHandler(tornado.web.RequestHandler):
    def get(self):
        tokenType = self.get_argument('type', 'UnKnown')
        # 获取token的口令
        secret = self.get_argument('secret', 'UnKnown')

        ret = {}
        if tokenType != 'UnKnown' and secret == config.requestSecret:
            try:
                # 从redis里查询
                valueInRedis = wechatRedis.get(tokenType)
                expireTime = wechatRedis.ttl(tokenType)
            except Exception as e:
                logger.error(e)
            finally:
                if valueInRedis is not None:
                    # token以二进制形式存在redis，这里需要做一个转码
                    ret[tokenType] = valueInRedis.decode('utf-8')
                    ret['expires_in'] = expireTime
                    logger.info('Query %s in redis sucess.', tokenType)
                else:
                    ret['error'] = 'not found'
        else:
            ret['error'] = 'invalid request'

        self.write(json.dumps(ret, sort_keys=False))


# 强制刷新token,适用于应用程序判断token已过期后主动刷新
class ForceRefreshHandler(tornado.web.RequestHandler):
    def get(self):
        tokenType = self.get_argument('type', 'UnKnown')
        # 获取token的口令
        secret = self.get_argument('secret', 'UnKnown')
        ret = {}
        if tokenType != 'UnKnown' and secret == config.requestSecret:
            request = renderRequest(tokenType)
            # 同步客戶端
            syncHttpClient = tornado.httpclient.HTTPClient()
            try:
                response = syncHttpClient.fetch(request)
            except Exception as e:
                logger.error('Exception: %s', e)
                logger.error('Force refresh %s failed.' % str(tokenType))
                ret['errmsg'] = str(e)
            else:
                logger.debug('Sync httpclient response: %s', response)
                logger.debug('Sync httpclient response body: %s', response.body)
                # response body里面json格式的字典
                resDict = json.loads(response.body.decode('utf8'))
                logger.info('Force refresh %s success, response is :%s' % (tokenType, resDict))
                token = resDict[tokenType]
                try:
                    # 存入redis数据库并设置过期时间
                    wechatRedis.set(tokenType, token, ex=config.tokenExpireTime)
                    logger.info('Set %s in redis success.', tokenType)
                except Exception as e:
                    logger.error(e)
                # 返回请求
                ret[tokenType] = resDict[tokenType]
                ret['expires_in'] = config.tokenExpireTime
            syncHttpClient.close()

        self.write(json.dumps(ret, sort_keys=False))


def makeApp():
    return tornado.web.Application([
        (r"/wechat/token", TokenHandler),
        (r"/wechat/token/forcerefresh", ForceRefreshHandler),
        (r"/", MainHandler),
    ])


def renderArgs(argsValue):
    # {{...}}里面是要渲染的值，需要从redis里查询，其他的直接返回实际值
    if argsValue.startswith('{{') and argsValue.endswith("}}"):
        argsValue = argsValue.strip('{}')
        # 从redis里查询
        valueInRedis = wechatRedis.get(argsValue)
        if valueInRedis is None:
            raise Exception("Cannot find %s in redis, render error." % argsValue)
        logger.info('{{%s}} render success, result: %s' % (argsValue, valueInRedis))
        return valueInRedis
    else:
        return argsValue


# 配置请求的网址和方法
def renderRequest(tokenType):
    args = {}
    for (k, v) in config.tokenSources[tokenType]['args'].items():
        # 解析参数
        args[k] = renderArgs(v)
        # 请求的网址
    url = tornado.httputil.url_concat(config.tokenSources[tokenType]['url'], args)
    request = tornado.httpclient.HTTPRequest(url, method=config.tokenSources[tokenType]['method'])
    return request



async def refreshToken(tokenType):
    # 异步客户端
    asyncHttpClient = tornado.httpclient.AsyncHTTPClient()
    request = renderRequest(tokenType)
    try:
        response = await asyncHttpClient.fetch(request)

    except Exception as e:
        logger.error('Exception: %s', e)
        logger.error('Create a request for %s failed, will retry after 10s' % str(tokenType))
        # 请求失败后10s后再次尝试刷新
        tornado.ioloop.IOLoop.instance().call_later(10, refreshToken, tokenType)
    else:
        logger.debug('Async httpclient response: %s', response)
        logger.debug('Async httpclient response body: %s', response.body)
        # response body里面json格式的字典
        resDict = json.loads(response.body.decode('utf8'))
        logger.info('Request %s success, response is :%s' % (tokenType, resDict))
        token = resDict[tokenType]
        # logger.info('Token value is %s', token)
        try:
            # 存入redis数据库并设置过期时间
            wechatRedis.set(tokenType, token, ex=config.tokenExpireTime)
            logger.info('Set %s in redis success.', tokenType)
        except Exception as e:
            logger.error(e)


# 依次刷新tokenSources中的token
async def refreshAllTokens():
    logger.info('Begin to refresh all tokens...')
    while True:
        for tokenType in config.tokenSources.keys():
            await refreshToken(tokenType)
        # 定时更新
        await tornado.gen.sleep(config.tokenExpireTime * 1000)


if __name__ == "__main__":
    app = makeApp()
    app.listen(config.bindPort, address=config.bindIp)
    # 自动刷新token
    tornado.ioloop.IOLoop.instance().spawn_callback(refreshAllTokens)
    tornado.ioloop.IOLoop.instance().start()
