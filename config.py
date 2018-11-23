#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author : yasin
# @time   : 11/20/18 7:30 PM
# @File   : config.py

import logging.config
logging.config.fileConfig("logger.conf")
logger = logging.getLogger("wechat-access-token-server")

tokenSources = {}
bindIp = '0.0.0.0'
bindPort = 12123

# 微信access_token配置示例
tokenSources['accesstoken'] = {
    'url': 'https://api.weixin.qq.com/cgi-bin/token',
    'method': 'GET',
    'args': {
        'grant_type': 'client_credential',
        'appid': '**************',
        'secret': '**********************'
    },
}

# 微信jsticket配置示例
tokenSources['jsticket'] = {
    'url': 'https://api.weixin.qq.com/cgi-bin/ticket/getticket',
    'method': 'GET',
    'args': {
        'type': 'jsapi',
        'access_token': '{{results.accesstoken.access_token}}'
    },
}
