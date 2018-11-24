#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author : yasin
# @time   : 11/20/18 7:30 PM
# @File   : main.py

import tornado.ioloop
import tornado.web
import tornado.httpclient
import tornado.httputil
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
        ret = {}
        if tokenType != 'UnKnown':
            try:
                # 从redis里查询
                valueInRedis = wechatRedis.get(tokenType)
            except Exception as e:
                logger.error(e)
            finally:
                if valueInRedis is not None:
                    # token以二进制形式存在redis，这里需要做一个转码
                    ret = valueInRedis.decode('utf-8')
                    logger.info('Query %s in redis sucess.', tokenType)
                else:
                    ret['error'] = 'not found'
        else:
            ret['error'] = 'unknown arguments'

        self.write(ret)


def makeApp():
    return tornado.web.Application([
        (r"/token/wechat", TokenHandler),
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


def refreshToken(tokenType):
    # request回调
    def handle(response):
        logger.debug('Async httpclient response: %s', response)
        logger.debug('Async httpclient response body: %s', response.body)

        if response.code == 200:
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
        else:
            logger.error('Request %s error, will retry after 10s' % tokenType)
            tornado.ioloop.IOLoop.instance().call_later(10, refreshToken, tokenType)

    try:
        args = {}
        for (k, v) in config.tokenSources[tokenType]['args'].items():
            # 解析参数
            args[k] = renderArgs(v)
        # 请求的网址
        url = tornado.httputil.url_concat(config.tokenSources[tokenType]['url'], args)
        # 异步客户端
        asyncHttpClient = tornado.httpclient.AsyncHTTPClient()
        # 配置请求的网址和方法
        request = tornado.httpclient.HTTPRequest(url, method=config.tokenSources[tokenType]['method'])
        # 发起请求并设置回调
        asyncHttpClient.fetch(request, callback=handle)

    except Exception as e:
        logger.error('Exception: %s', e)
        logger.error('Create a request for %s failed, will retry after 10s' % str(tokenType))
        # 请求失败后10s后再次尝试刷新
        tornado.ioloop.IOLoop.instance().call_later(10, refreshToken, tokenType)


# 依次刷新tokenSources中的token
def refreshAllTokens():
    logger.info('Begin to refresh all tokens...')

    for tokenType in config.tokenSources.keys():
        refreshToken(tokenType)


if __name__ == "__main__":
    app = makeApp()
    app.listen(config.bindPort, address=config.bindIp)
    # 启动前先刷新一次
    tornado.ioloop.IOLoop.instance().add_callback(refreshAllTokens)
    # 开启定时任务，过期时间到后就刷新一次
    tornado.ioloop.PeriodicCallback(refreshAllTokens, config.tokenExpireTime * 1000).start()
    tornado.ioloop.IOLoop.instance().start()
