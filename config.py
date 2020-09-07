#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author : yasin
# @time   : 11/20/18 7:30 PM
# @File   : config.py

from log import get_logger

# 日志配置
LOG_NAME = 'wechat-token-server'
LOG_CMD_LEVEL = 'INFO'
LOG_FILE_LEVEL = 'INFO'
logger = get_logger(loggername=LOG_NAME, filename='./logs/' + LOG_NAME + '.log')
logger.set_logger(cmdlevel=LOG_CMD_LEVEL)
logger.set_logger(filelevel=LOG_FILE_LEVEL)


tokenSources = {}
tokenExpireTime = 7000

bindIp = '0.0.0.0'
bindPort = 12123

redisIp = '127.0.0.1'
redisPort = 6379

# 获取token的口令
requestSecret = 'f3b2241f967aa3c7966f537cdd82ce11'

# 微信access_token配置示例
tokenSources['access_token'] = {
    'url': 'https://api.weixin.qq.com/cgi-bin/token',
    'method': 'GET',
    'args': {
        'grant_type': 'client_credential',
        'appid': '**************',
        'secret': '**********************'
    },
}

# 微信jsticket配置示例
tokenSources['ticket'] = {
    'url': 'https://api.weixin.qq.com/cgi-bin/ticket/getticket',
    'method': 'GET',
    'args': {
        'type': 'jsapi',
        'access_token': '{{access_token}}'
    },
}
