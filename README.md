# api_oop_ten_jwt.py 代码理解
---
## JWT部份
**jwt是什么**

- jwt 全称是 JSON Web Token，是一种用于在网络上安全传输信息的标准。它通常用于身份验证和授权。

- 在代码中，我们使用了 PyJWT 库来实现 JWT 加密和解密。PyJWT 是一个 Python 库，用于处理 JSON Web Token。它提供了许多有用的功能，例如创建、验证和解码 JWT，以及对 JWT 进行签名和验证

**jwt的结构**
- jwt 的结构通常包含三个部分：头部、载荷和签名。Header.Payload.Signature

**1: Header（头部）**
> 代码示例
```python
{
  "alg": "HS256",
  "typ": "JWT"
}
```
- alg 是算法algorithm的缩写，表示加密算法。此处的值为 HS256，表示使用 HMAC SHA-256 算法进行签名。
- 而 HMAC 是一种基于哈希函数的消息认证码，借助一个密钥和哈希算法[^1]

-typ 是类型的缩写，表示令牌的类型。此处的值为 JWT，表示这是一个 JWT 令牌。<u>非必要项</u>,作用是让接收方快速的识别到这个是一个jwt，而不是一个普通的字符串，然后惊醒快速处理 

**2: Payload（载荷）**
- jwt中的payload部份是jwt的核心组成部份，主要是承载着用户的声明，chaims
- 声明有不同的类型可以分为：
    - 1.注册声明：（registration claims）：用于存储用户注册时的信息，例如用户名、邮箱、密码等。这些信息通常不会被公开，因为它们可能包含敏感信息。
        - iss（issuer）：签发人，表明jwt签发的主体，例如可以是网站的一个域名
        - exp（expiration time）：过期时间，超过这个时间后，jwt将失效
        - sub（subject）：主题，用户的唯一标识符，例如可以是用户在网站上的唯一标识符
        - aud（audience）：受众，表明jwt的接收方，也可以是一个网站的域名
        - nbf（not before）：生效时间，在这个时间前，jwt不可用
        - iat（issued at）：签发时间，jwt的签发时间
        - jti（JWT ID）：JWT 的唯一标识符，防止被重复利用
    - 2.身份声明：（identity claims）：用于存储用户身份信息，例如用户ID、用户名、用户角色等。这些信息通常会被公开，因为它们是用户身份的标识符。
    - 3.访问声明：（access claims）：用于存储用户访问资源的信息，例如用户权限、角色等。这些信息通常会被公开，因为它们是用户访问资源的权限标识符。
    - 4.其他
> 代码示例
```python
{
    "iss": "https://example.com",#签发人
    "sub": "1234567890",  #主题
    "aud": "client_app",  #受众
    "exp": 1679232000[^2],    #过期时间
    "nbf": 1679145600,    #生效时间
    "iat": 1679145600,    #签发时间
    "jti": "abcdef123456", #JWT ID
    "name": "John Doe",   #身份声明
    "email": "johndoe@example.com", #身份声明
    "custom_claim": "custom_value" #访问声明
}
```
- payload同样也会被转化成json字符串，进行base64url编码，然后拼接在一起，形成一个完整的jwt字符串，<U>需要注意的是，没有加密，任何人都可以对其进行解码</U>，所以不要将敏感信息放在payload中，如密码等。

> 代码示例
```python
import jwt
from datetime import datetime, timedelta

# 定义Payload
payload = {
    "iss": "https://example.com",
    "sub": "1234567890",
    "aud": "client_app",
    "exp": datetime.utcnow() + timedelta(minutes=30)#生成时间30分钟后过期
    "nbf": datetime.utcnow(),#生效时间
    "iat": datetime.utcnow(),#签发时间
    "jti": "abcdef123456",
    "name": "John Doe",
    "email": "johndoe@example.com",
    "custom_claim": "custom_value"
}

# 定义秘钥
secret_key = "your_secret_key"

# 生成JWT
token = jwt.encode(payload, secret_key, algorithm="HS256")

print("生成的JWT:", token)
```
- 此程序中，自定义了一个payload，定义了一个密钥，算法为Hs256，然后使用jwt.encode函数生成了一个jwt字符串，最后打印出了生成的jwt字符串。

**3: Signature（签名）**
- jwt中的signature部份是jwt的核心组成部份，用于验证jwt的合法性，通过将payload和秘钥进行加密，生成一个签名

- 要创建签名，需要用到编码后的header，payload，密钥，和算法

- 签名的生成过程如下：
    1. 将header和payload进行base64url编码
    2. 将编码后的header和payload拼接在一起，中间用点（.）分隔
    3. 将拼接后的字符串和密钥进行HMAC SHA-256加密
    4. 将加密后的结果进行base64url编码，得到签名
    5. 将签名拼接在payload和header后面，中间用点（.）分隔，形成完整的jwt字符串
   
- 常见的签名算法：
    - HS256：HMAC SHA-256
    - HS384：HMAC SHA-384
    - HS512：HMAC SHA-512

- 签名的作用是确保jwt的完整性和不可篡改性，防止jwt被篡改或伪造。


## 代码JWT部份讲解
1. **JWT生成部份**
> python
```python
@app.route('/login', methods=['POST'])
def login():
    # 从数据库验证用户信息
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute('SELECT password FROM users WHERE username = ?', (username,))
            result = c.fetchone()
            if result:
                stored_password = result[0]
                if stored_password == password:
                    # 生成JWT
                    payload = {
                        'user': username,
                        'exp': datetime.utcnow() + timedelta(minutes=30)
                    }
                    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
                    return jsonify({'token': token})
    except sqlite3.Error as e:
        logging.error(f"登录时查询数据库出错： {e}")

    return jsonify({'error': 'Invalid credentials'}), 401
```
- 这段代码是一个登录接口，当用户输入用户名和密码时，会从数据库中查询用户信息，然后验证密码是否正确。如果密码正确，就会生成一个JWT，并将其返回给客户端。
- 首先，从客户端获取用户名跟密码，然后通过get_db_connection()函数获取数据库连接，查询语句，如果用户名跟密码符合数据库的内容，就准备生成jwt
> 生成jwt部份
```python
# 生成JWT
# 密钥，用于JWT签名和验证
SECRET_KEY = "a_showiix_showiix_showiix_showiix_1234567890abcdef"
payload = {
    'user': username, #用户信息
    'exp': datetime.utcnow() + timedelta(minutes=30)
    } #过期时间30分钟后过期
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    # 生成jwt，第一个参数是payload，第二个参数是密钥，第三个参数是算法
    return jsonify({'token': token})
    # 将生成的jwt以json的格式返回客户端
```

2: **JWT验证部份**
> python
```python
# JWT验证装饰器
def token_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token!'}), 401
        return f(*args, **kwargs)
    return decorated
```
- 从请求的头部信息中获取'Authorization'字段的值，这个值通常是一个以'Bearer '开头的字符串，后面跟着JWT。
- 如果'Authorization'字段不存在，说明请求中没有提供JWT，返回一个401状态码，表示未授权。
- 如果'Authorization'字段存在，将其值中的'Bearer '前缀去掉，得到JWT。
- 使用docode方法对token进行解码，使用SECRET_KEY作为密钥，使用HS256算法进行验证。
- 如过时间过期，返回一个401状态码，表示未授权。
- 如果token验证通过，将解码后的payload作为参数传递给被装饰的函数，并执行该函数。
- 如果token验证失败，返回一个401状态码，表示未授权。
- 这个装饰器可以用于保护需要身份验证的API接口，只有在请求中提供有效的JWT时，才能访问被装饰的函数。

## 总结—通俗易懂的方式了解jwt实现过程
**1.jwt生成**
用户登录系统的时候，系统会验证用户名跟密码是否跟在数据库中注册的用户匹配，如果匹配了，系统就会生成一个jwt，相当于一个身份证，在api_oop_ten_jwt.py中，用户通过login接口进入，post语句将用户名跟密码作为参数传入，系统若匹配成功，就会把用户名跟过期时间放在jwt的负载部份payload，然后用密钥，算法对他进行加密，生成签名，然后将签名，负载，头部拼接在一起，形成一个完整的jwt字符串，然后将这个jwt字符串返回给客户端。

**2.用户访问**
用户拿到jwt之后，如果需要访问被jwt修饰的api端口，则需要在jwt放在请求头部的Authorization字段中然后系统会获取，这个字段的值通常是在Bearer 后面

**3.jwt验证**
系统会提取到这个jwt，先看看是不是空的，如果是空的就直接报错，如果存在，他就会拿掉Bearer前缀，用之前生成的密钥进行解码，如果发现过期，不会通过，如果发现被修改了，也不会通过，如果通过了，就返回一个payload，然后在被装饰的函数中，将这个payload作为参数传递给被装饰的函数，然后执行该函数。

## 密钥泄露
1:伪造jwt
    - 密钥泄露可能导致jwt被伪造，因为如果密钥泄露，那么任何一个人都可以生成一个jwt，然后将这个jwt传递给系统，系统就会认为这个jwt是合法的，然后执行被装饰的函数。
2:篡改jwt
    - 密钥泄露可能导致jwt被篡改，因为如果密钥泄露，那么任何一个人都可以修改jwt，然后将这个jwt传递给系统，系统就会认为这个jwt是合法的，然后执行被装饰的函数
3:信息泄露
    - 密钥泄露可能导致jwt中的信息泄露，因为如果密钥泄露，那么任何一个人都可以查看jwt中的信息，然后将这个jwt传递给系统，系统就会认为这个jwt是合法的，然后执行被装饰的函数

定期修改，或者结合一些其他的验证方式




[^1]:SHA-256 算法的摘要函数，用于将消息转换为一个固定长度的哈希值。它是一种不可逆的哈希函数，用于生成消息的摘要，用于验证消息的完整性。
[^2]:exp 是过期时间，它是一个 Unix 时间戳，可以在python代码中用datatime模块去转化

  





