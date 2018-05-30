import functools
from flask import Blueprint, session, make_response, jsonify, render_template, redirect

# 首页不加前缀
from flask import current_app
from flask import request

from models import UserInfo, db

user_blueprint = Blueprint('user', __name__, url_prefix='/user')


@user_blueprint.route('/image_yzm')
def image_yzm():
    from utils.captcha.captcha import captcha
    # name表示一个随机名称, yzm表示验证码字符串, buffer是图片的二进制数据
    name, yzm, buffer = captcha.generate_captcha()

    # 把验证码存入session,用于后续请求的时候对比
    session['image_yzm'] = yzm

    # 将图片数据返回，浏览器会默认按text/html解析，需要设置为image/png
    response = make_response(buffer)
    response.mimetype = 'image/png'

    return response


@user_blueprint.route('/sms_yzm')
def sms_yzm():
    # 获取数据：手机号，图片码
    dict1 = request.args
    mobile = dict1.get('mobile')
    # 忽略大小写
    image_yzm = dict1.get('image_yzm').upper()
    print(image_yzm)

    # 对比图片验证码
    if image_yzm != session['image_yzm']:
        return jsonify(result=1)

    # 随机生成一个数字
    import random
    yzm = random.randint(1000, 9999)

    # 保存到session
    session['sms_yzm'] = yzm

    from utils.ytx_sdk import ytx_send
    # ytx_send.sendTemplateSMS(mobile,{yzm,5},1) # 手机号,{验证码,过期时间},用什么模板默认为1
    print(yzm)

    return jsonify(result=2)


@user_blueprint.route('/register', methods=['POST'])
def register():
    # 1.接收数据
    dict1 = request.form
    mobile = dict1.get('mobile')
    image_yzm = dict1.get('image_yzm').upper()
    sms_yzm = dict1.get('sms_yzm')
    pwd = dict1.get('pwd')

    # 2.验证数据的有效性
    if not all([mobile, image_yzm, sms_yzm, pwd]):
        return jsonify(result=1)
    if image_yzm != session['image_yzm']:
        return jsonify(result=2)
    if int(sms_yzm) != session['sms_yzm']:
        return jsonify(result=3)

    import re
    if not re.match(r'[a-zA-Z0-9_]{6,20}', pwd):
        return jsonify(result=4)

    mobile_count = UserInfo.query.filter_by(mobile=mobile).count()
    if mobile_count > 0:
        return jsonify(result=5)

    # 3.创建对象
    user = UserInfo()
    user.nick_name = mobile
    user.mobile = mobile
    user.password = pwd

    # 4.提交
    try:
        # 把user对象添加到session
        db.session.add(user)
        # 提交即保存到数据库
        db.session.commit()
    except:
        current_app.logger_xjzx.error('注册用户时数据库访问失败')
        return jsonify(result=6)

    # 返回响应（成功）
    return jsonify(result=7)


@user_blueprint.route('/login', methods=['POST'])
def login():
    # 接收
    dict1 = request.form
    mobile = dict1.get('mobile')
    pwd = dict1.get('pwd')
    # 验证
    if not all([mobile, pwd]):
        return jsonify(result=1)

    # 处理：查询
    user = UserInfo.query.filter_by(mobile=mobile).first()

    if user:
        if user.check_pwd(pwd):
            # 登陆成功，状态保持
            session['user_id'] = user.id
            # 将头像，昵称返回给浏览器显示
            return jsonify(result=3, avatar_url=user.avatar_url, nick_name=user.nick_name)
        else:
            # 密码错误
            return jsonify(result=4)
    else:
        # mobile错误
        return jsonify(result=2)


@user_blueprint.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id')
    return jsonify(result=1)


# 定义验证登陆的装饰器
def login_required(f):
    @functools.wraps(f)  # 返回f函数的名称，而不是用fun2替代这个函数的名称
    def fun2(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/')
        # 在视图函数上添加的装饰器，必须要将视图返回的response再次返回给浏览器
        return f(*args, **kwargs)

    return fun2


@user_blueprint.route('/')
@login_required
def index():
    # 从session中获取用户编号，创建user对象，传给模板显示
    user = UserInfo.query.get(session['user_id'])
    return render_template('news/user.html',
                           user=user,
                           title='用户中心')


# 定义用户视图
# 基本资料
@user_blueprint.route('/base', methods=['GET', 'POST'])
@login_required
def base():
    # 获取当前用户编号
    user_id = session['user_id']
    # 查询当前用户对象
    user = UserInfo.query.get(user_id)

    # 如果是get请求，展示数据
    if request.method == 'GET':
        return render_template('news/user_base_info.html', user=user)
    # 如果是post请求则修改数据并保存
    elif request.method == 'POST':
        # 接收数据
        dict1 = request.form
        signature = dict1.get('signature')
        nick_name = dict1.get('nick_name')
        gender = dict1.get('gender')
        # 根据user_id查询数据，并修改
        user.signature = signature
        user.nick_name = nick_name
        user.gender = True if gender == 'True' else False
        # 提交保存
        try:
            db.session.commit()
        except:
            current_app.logger_xjzx.error('修改用户基本信息时连接数据库失败')
            return jsonify(result=2)
        # 响应
        return jsonify(result=1)


@user_blueprint.route('/pic', methods=['GET', 'POST'])
@login_required
def pic():
    user = UserInfo.query.get(session['user_id'])
    if request.method == 'GET':
        return render_template('news/user_pic_info.html', user=user)
    elif request.method == 'POST':
        # 接收文件
        f1 = request.files.get('avatar')
        # 保存文件到骑牛云，并返回文件名
        from utils.qiniu_xjzx import upload_pic
        f1_name = upload_pic(f1)
        # 将文件名保存到数据库
        user.avatar = f1_name
        # 提交
        db.session.commit()
        # 响应
        return jsonify(result=1, avatar_url=user.avatar_url)


@user_blueprint.route('/follow', methods=['GET', 'POST'])
@login_required
def follow():
    pass


@user_blueprint.route('/pwd', methods=['GET', 'POST'])
@login_required
def pwd():
    pass


@user_blueprint.route('/collect', methods=['GET', 'POST'])
@login_required
def collect():
    pass


@user_blueprint.route('/release', methods=['GET', 'POST'])
@login_required
def release():
    pass


@user_blueprint.route('/newslist', methods=['GET', 'POST'])
@login_required
def newslist():
    pass
