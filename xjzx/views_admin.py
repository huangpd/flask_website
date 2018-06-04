from datetime import datetime

from flask import Blueprint
from flask import abort
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session

from models import UserInfo,NewsInfo

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')


@admin_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('admin/login.html')
    elif request.method == 'POST':
        # 接收
        dict1 = request.form
        mobile = dict1.get('username')
        pwd = dict1.get('password')
        # 验证
        if not all([mobile, pwd]):
            abort(404)
        # 处理
        user = UserInfo.query.filter_by(isAdmin=True, mobile=mobile).first()
        # 判断账号是否存在
        if user is None:
            return render_template(
                'admin/login.html',
                mobile=mobile,
                pwd=pwd,
                msg='账号错误'
            )
        # 判断密码是否正确
        if user.check_pwd(pwd):
            session['admin_user_id'] = user.id
            return redirect('/admin/')
        else:
            return render_template(
                'admin/login.html',
                mobile=mobile,
                pwd=pwd,
                msg='密码错误'
            )


# 使用请求勾子，进行登录验证
# 使用蓝图注册钩子，表示只有在请求这个蓝图的视图时，才会执行这个请求勾子
@admin_blueprint.before_request
def before_request():
    # 判断是否访问登陆视图，如果是则不需要验证
    if request.path != '/admin/login':
        if 'admin_user_id' not in session:
            return redirect('/admin/login')
        # 使用g变量，就表示一次请求响应中的全局变量
        # 一般结合勾子使用，设置后可以在视图、模板中访问这个值
        g.user = UserInfo.query.get(session['admin_user_id'])


# 管理员登陆
@admin_blueprint.route('/')
def index():
    return render_template(
        'admin/index.html'
    )


# 注销
@admin_blueprint.route('/logout')
def logout():
    del session['admin_user_id']
    return redirect('/admin/login')


@admin_blueprint.route('/user_count')
def user_count():
    # 用户总数
    user_total = UserInfo.query.filter_by(isAdmin=False).count()
    # 用户月新增数
    '''
    分析：
    统计某月的注册量，即从y-m-1 00:00:00开始
    只要比这个时间大的，就是本月的
    '''
    now = datetime.now()
    month_first = datetime(now.year, now.month, 1)
    user_month = UserInfo.query.filter_by(isAdmin=False). \
        filter(UserInfo.create_time >= month_first).count()
    # 用户日新增数
    day_first = datetime(now.year, now.month, now.day)
    user_day = UserInfo.query.filter_by(isAdmin=False). \
        filter(UserInfo.create_time >= day_first).count()
    # 用户小时登陆活跃数
    # 从redis中取表：key
    key = 'login%d_%d_%d' % (now.year, now.month, now.day)
    # 拿到key表中所有的键名，即各个时间段
    hour_list = current_app.redis_client.hkeys(key)
    # 推导式解码
    hour_list = [hour.decode() for hour in hour_list]
    # 拿到每个hour的活跃数存在列表中用来展示
    count_list = []
    for hour in hour_list:
        count_list.append(int(current_app.redis_client.hget(key, hour)))

    return render_template(
        'admin/user_count.html',
        user_total=user_total,
        user_month=user_month,
        user_day=user_day,
        hour_list=hour_list,
        count_list=count_list
    )


@admin_blueprint.route('/user_list')
def user_list():
    page = int(request.args.get('page', '1'))
    pagenation = UserInfo.query.filter(UserInfo.isAdmin == False). \
        order_by(UserInfo.id.desc()).paginate(page, 9, False)
    user_list1 = pagenation.items
    total_page = pagenation.pages

    return render_template(
        'admin/user_list.html',
        page=page,
        user_list1=user_list1,
        total_page=total_page
    )


@admin_blueprint.route('/news_review')
def news_review():
    page = int(request.args.get('page', '1'))
    pagenation = NewsInfo.query.order_by(NewsInfo.id).paginate(page, 10, False)
    news_list = pagenation.items
    total_page = pagenation.pages

    return render_template(
        'admin/news_review.html',
        page=page,
        news_list=news_list,
        total_page=total_page
    )


@admin_blueprint.route('/news_edit')
def news_edit():
    return render_template(
        'admin/news_edit.html'
    )


@admin_blueprint.route('/news_type')
def news_type():
    return render_template(
        'admin/news_type.html'
    )
