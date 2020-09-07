### wechat-token-server
微信token中控服务器，用于统一获取并缓存微信开发中使用的access_token和jsticket。  

wechat-token-server是一个自动定时刷新微信token的服务，可以每隔一段时间自动获取token，保存在redis中，通过访问redis或web接口即可获取到缓存的token值。同时用户也可以主动刷新。

#### 实现功能（微信官方建议）
- 建议公众号开发者使用中控服务器统一获取和刷新Access_token，其他业务逻辑服务器所使用的access_token均来自于该中控服务器，不应该各自去刷新，否则容易造成冲突，导致access_token覆盖而影响业务；

- 目前Access_token的有效期通过返回的expire_in来传达，目前是7200秒之内的值。中控服务器需要根据这个有效时间提前去刷新新access_token。在刷新过程中，中控服务器可对外继续输出的老access_token，此时公众平台后台会保证在5分钟内，新老access_token都可用，这保证了第三方业务的平滑过渡；

- Access_token的有效时间可能会在未来有调整，所以中控服务器不仅需要内部定时主动刷新，还需要提供被动刷新access_token的接口，这样便于业务服务器在API调用获知access_token已超时的情况下，可以触发access_token的刷新流程。

#### 配置
修改config.py即可，下面是各配置选项含义。  

```tokenExpireTime``` : 中控服务器自己缓存的token过期时间  
```bindIp```  :tornado服务器绑定的IP  
```bindPort``` : 绑定端口  
```redisIp``` :redis服务器运行IP  
```redisPort``` : redis服务器运行端口  
```requestSecret``` : 获取token的口令    
```appid``` :公众号或小程序应用ID  
```secret``` : 应用秘钥    

示例代码：
```python
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
requestSecret = '*******'

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
```
#### 运行与使用
##### 环境与依赖项
- Ubuntu16.04
- Python 3.6
- tornado==5.1.1
- redis==3.0.1
##### 后台运行
```nohup python3 token_server.py & ```

##### 通过redis查询
如果查询程序与wechat token sever运行在同一台机器上，可以直接查询redis服务器，键值就是```access_token```和```ticket```。

##### 通过url访问
直接访问对应的url即可，secret为自己在config.py里面设置的```requestSecret``` 

- 查询access_token : ```http://127.0.0.1:12123/wechat/token?type=access_token&secret=f3b2241f967aa3c7966f537cdd82ce11```
- 查询jsticket : ```http://127.0.0.1:12123/wechat/token?type=ticket&secret=f3b2241f967aa3c7966f537cdd82ce11```
- 主动刷新access_token : ```http://127.0.0.1:12123/wechat/token/forcerefresh?type=access_token&secret=f3b2241f967aa3c7966f537cdd82ce11```
- 主动刷新jsticket : ```http://127.0.0.1:12123/wechat/token/forcerefresh?type=ticket&secret=f3b2241f967aa3c7966f537cdd82ce11```

##### 结果示例
查询access_token结果： ```{"access_token": "16_XLwKyOP2XSxwr1ZCB0tpaANb4l2cJSeJdr6aj0QQkQAp_v4q5E-eCIkmDyOcMU6V0aTSsXiJzyf-KwiVP0MHIv47XftDa_oSvCnH8jJfTz8POfBjTcl52jGBboPMoo-esVjCVW2Ll3D2_6RHAGEiAJAGMK", "expires_in": 3298}```

##### 反向代理设置
如果希望通过域名访问，可以使用Nginx设置反向代理，将你需要访问域名配置好后，访问指定的url直接转发到tornado运行的地址与端口即可。   
配置示例：
```
server {
    listen 443;
    server_name gitlab.net.cn;
    ssl on;
    root /home/yasin/html/domain/gitlab_net_cn;
    index index.html index.htm;
    ssl_certificate  /home/yasin/ssl/gitlab/gitlab.net.cn.crt;
    ssl_certificate_key /home/yasin/ssl/gitlab/gitlab.net.cn.key;
    ssl_session_timeout 5m;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE:ECDH:AES:HIGH:!NULL:!aNULL:!MD5:!ADH:!RC4;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers on;
    location / {
        proxy_pass http://127.0.0.1:12123;
    }
}

```
这样配置好后，在其他任地方直接访问```https://gitlab.net.cn/wechat/token?type=access_token&secret=f3b2241f967aa3c7966f537cdd82ce11```即可得到access_token值。
