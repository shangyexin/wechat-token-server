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

tokens = {}


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Welcome to use wechat access token server!")


class TokenHandler(tornado.web.RequestHandler):
    def get(self):
        name = self.get_argument('name', 'UnKnown')
        ret = {}
        if name not in tokens:
            ret['error'] = 'not found'
        else:
            ret = tokens[name]

        self.write(json.dumps(ret))


def makeApp():
    return tornado.web.Application([
        (r"/token", TokenHandler),
        (r"/", MainHandler),
    ])


def renderArgs(argsValue):
    # {{...}}里面是要渲染的值，需要从之前的请求中获取，其他的直接返回实际值
    if argsValue.startswith('{{') and argsValue.endswith("}}"):
        renderMap = {}
        # 获取当前token字典中的值
        renderMap['results'] = tokens

        argsValue = argsValue.strip('{}')
        idxs = argsValue.split('.')

        target = renderMap
        for idx in idxs:
            target = target[idx]

        if type(target) != str:
            raise Exception("render %s error" % argsValue)
        logger.info('{{%s}} render result: %s' % (argsValue, target))
        return target
    else:
        return argsValue


def refreshToken(group):
    # request回调
    def handle(response):
        logger.debug('Async httpclient response: %s', response)
        logger.debug('Async httpclient response body: %s', response.body)

        if response.code == 200:
            # response body里面json格式的字典
            resDict = json.loads(response.body.decode('utf8'))
            tokens[group] = resDict
            logger.info('Request %s success, response is :%s' % (group, tokens[group]))
        else:
            logger.error('Request %s error, will retry after 10s' % group)
            tornado.ioloop.IOLoop.instance().call_later(10, refreshToken, group)

    try:
        args = {}
        for (k, v) in config.tokenSources[group]['args'].items():
            # 解析参数
            args[k] = renderArgs(v)
        # 请求的网址
        url = tornado.httputil.url_concat(config.tokenSources[group]['url'], args)
        # 异步客户端
        asyncHttpClient = tornado.httpclient.AsyncHTTPClient()
        # 配置请求的网址和方法
        request = tornado.httpclient.HTTPRequest(url, method=config.tokenSources[group]['method'])
        # 发起请求并设置回调
        asyncHttpClient.fetch(request, callback=handle)

    except Exception as e:
        logger.error('Exception: %s', e)
        logger.error('Create a request for %s failed, will retry after 10s' % str(group))
        # 请求失败后10s后再次尝试刷新
        tornado.ioloop.IOLoop.instance().call_later(10, refreshToken, group)


# 依次刷新tokenSources中的token
def refreshAllTokens():
    logger.info('Begin to refresh all tokens...')

    for group in config.tokenSources.keys():
        refreshToken(group)


if __name__ == "__main__":
    app = makeApp()
    app.listen(config.bindPort, address=config.bindIp)
    # 启动前先刷新一次
    tornado.ioloop.IOLoop.instance().add_callback(refreshAllTokens)
    # 开启定时任务，以后每7000s刷新一次
    tornado.ioloop.PeriodicCallback(refreshAllTokens, 7000 * 1000).start()
    tornado.ioloop.IOLoop.instance().start()
