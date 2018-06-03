from flask import Blueprint, render_template, jsonify
from flask import abort
from flask import request
from flask import session
from flask import current_app

from models import db, NewsCategory, UserInfo, NewsInfo, NewsComment

# 首页不加前缀
news_blueprint = Blueprint('news', __name__)


# 首页
@news_blueprint.route('/')
def index():
    category_list = NewsCategory.query.all()

    # 查询点击量最高的6条数据==>select * from ... order by ... limit 0,6
    count_list = NewsInfo.query.order_by(NewsInfo.click_count.desc())[0:6]

    if 'user_id' in session:
        user = UserInfo.query.get(session['user_id'])
    else:
        user = None
    return render_template(
        'news/index.html',
        title='首页',
        category_list=category_list,
        user=user,
        count_list=count_list
    )


@news_blueprint.route('/newslist')
def newslist():
    # 接收页码
    page = int(request.args.get('page', '1'))
    # 接收分类编号
    category_id = int(request.args.get('category', '0'))

    pagination = NewsInfo.query
    # 进行制定分类的查询
    if category_id:
        pagination = pagination.filter_by(category_id=category_id)
    pagination = pagination.order_by(NewsInfo.create_time.desc()).paginate(page, 4, False)
    news_list = pagination.items

    # 因为NewsInfo类型的对象，在js中是无法识别的，所以需要改成字典对象再返回
    news_list2 = []
    for news in news_list:
        news_dict = {
            'id': news.id,
            'title': news.title,
            'summary': news.summary,
            'pic_url': news.pic_url,
            'user_avatar': news.user.avatar_url,
            'user_id': news.user.id,
            'user_nick_name': news.user.nick_name,
            'create_time': news.create_time,
            'category_id': news.category_id
        }
        news_list2.append(news_dict)

    return jsonify(
        page=page,
        news_list=news_list2
    )


@news_blueprint.route('/<int:news_id>')
def detail(news_id):
    news = NewsInfo.query.get(news_id)

    if news is None:
        abort(404)

    # 判断登陆状态
    if 'user_id' in session:
        user = UserInfo.query.get(session['user_id'])
    else:
        user = None

    # 查询点击量最高的6条数据==>select * from ... order by ... limit 0,6
    count_list = NewsInfo.query.order_by(NewsInfo.click_count.desc())[0:6]

    return render_template(
        'news/detail.html',
        news=news,
        title='文章详情页',
        user=user,
        count_list=count_list,
    )


@news_blueprint.route("/collect/<int:news_id>", methods=['POST'])
def collect(news_id):
    # action：是否收藏,默认为1
    action = int(request.form.get('action', '1'))
    # 获取当前新闻对象
    news = NewsInfo.query.get(news_id)
    if news is None:
        return jsonify(result=1)
    # 判断是否登陆
    if 'user_id' not in session:
        return jsonify(result=2)
    # 获取当前用户对象
    user = UserInfo.query.get(session['user_id'])

    # 判断是收藏还是取消
    if action == 1:
        # 判断当前是否已经被收藏，是则忽略
        if news in user.news_collect:
            return jsonify(result=4)
        # 添加收藏,添加新闻对象
        user.news_collect.append(news)
    else:
        # 判断当前是否已经被收藏，不是则忽略
        if news not in user.news_collect:
            return jsonify(result=4)
        # 取消收藏，从列表中删除数据
        user.news_collect.remove(news)
    # 提交到数据库
    db.session.commit()
    # 响应
    return jsonify(result=3)


@news_blueprint.route('/comment/add', methods=['POST'])
def commentadd():
    # 接收数据：新闻编号，评论内容
    dict1 = request.form
    news_id = dict1.get('news_id')
    msg = dict1.get('msg')
    # 验证
    if not all([news_id, msg]):
        return jsonify(result=1)
    news = NewsInfo.query.get(news_id)
    # 判断新闻对象是否存在
    if news is None:
        return jsonify(result=2)
    # 判断登陆状态
    if 'user_id' not in session:
        return jsonify(result=3)
    # 评论量+1
    news.comment_count += 1
    # 保存
    comment = NewsComment()
    comment.news_id = int(news_id)
    comment.user_id = session['user_id']
    comment.msg = msg
    db.session.add(comment)
    db.session.commit()
    # 响应
    return jsonify(result=4, comment_count=news.comment_count)


@news_blueprint.route('/comment/list/<int:news_id>')
def commentlist(news_id):
    # 根据新闻编号，查询对应的评论信息

    # 接受当前页码值参数
    # page = int(request.args.get('page', '1'))
    # 对数据进行分页
    # pagination = NewsComment.query.filter_by(news_id=news_id).order_by(NewsComment.like_count.desc(),
    #                                                                    NewsComment.create_time.desc()).paginate(page, 4,
    #                                                                                                             False)
    # 获取当前页的数据
    # comment_list = pagination.items
    comment_list = NewsComment.query.filter_by(news_id=news_id, comment_id=None). \
        order_by(NewsComment.like_count.desc(), NewsComment.create_time.desc())
    # 获取总页数
    # total_page = pagination.pages


    # 获取当前用户点赞列表
    if 'user_id' in session:
        user_id = session['user_id']
        commentid_list = current_app.redis_client.lrange('commentup%d' % user_id, 0, -1)
        # 将列表中的元素由byte转成int
        commentid_list = [int(cid) for cid in commentid_list]
    else:
        commentid_list = []

    # 把数据转换成字典格式返回给浏览器
    comment_list2 = []
    for comment in comment_list:
        # 获取当前用户是否对这个评论点赞
        if comment.id in commentid_list:
            is_like = 1
        else:
            is_like = 0
        comment_dict = {
            'id': comment.id,
            'like_count': comment.like_count,
            'msg': comment.msg,
            'create_time': comment.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            # UserInfo中的comments的属性的反向引用
            'nick_name': comment.user.nick_name,
            'avatar': comment.user.avatar_url,
            'is_like': is_like
        }

        # 对评论的回复也放在v-for中循环显示
        cback_list = []
        # TODO 这里的comment为什么可以点comments
        for cback in comment.comments:
            cback_dict = {
                'nick_name': cback.user.nick_name,
                'msg': cback.msg
            }
            cback_list.append(cback_dict)
        comment_dict['cback_list'] = cback_list

        comment_list2.append(comment_dict)

    return jsonify(
        comment_list=comment_list2,
        # comment_list1=comment_list1,
        # page=page,
        # total_page=total_page
    )


@news_blueprint.route('/commentup/<int:comment_id>', methods=['POST'])
def commentup(comment_id):
    # 接手操作行为，1为点赞，2为取消
    action = int(request.form.get('action', '1'))
    # 获取用户的编号
    if 'user_id' not in session:
        return jsonify(result=2)
    user_id = session['user_id']
    # 将评论的点赞数量+1
    comment = NewsComment.query.get(comment_id)
    if action == 1:
        comment.like_count += 1
    else:
        comment.like_count -= 1
    db.session.commit()

    if action == 1:
        current_app.redis_client.rpush('commentup%d' % user_id, comment_id)
    else:
        current_app.redis_client.lrem('commentup%d' % user_id, 0, comment_id)

    return jsonify(result=1, like_count=comment.like_count)


@news_blueprint.route('/commentback/<int:comment_id>', methods=['POST'])
def commentback(comment_id):
    # 用户user_id回复了评论comment_id，内容为msg
    msg = request.form.get('msg')
    news_id = int(request.form.get('news_id'))
    if not all([msg]):
        return jsonify(result=1)
    if 'user_id' not in session:
        return jsonify(result=2)
    user_id = session['user_id']
    # 创建评论对象
    comment = NewsComment()
    comment.news_id = news_id
    comment.user_id = user_id
    comment.comment_id = comment_id
    comment.msg = msg
    # 提交数据库
    db.session.add(comment)
    db.session.commit()
    return jsonify(result=3)


@news_blueprint.route('/userfollow', methods=['POST'])
def userfollow():
    # 当前登录用户user_id关注作者 follow_user_id
    # 处理1：向对象的列表中添加对象
    action = int(request.form.get('action', '1'))
    follow_user_id = request.form.get('follow_user_id')
    follow_user = UserInfo.query.get(follow_user_id)
    # 将user_id加到login_user，follow_user即是被login_user关注的人
    if 'user_id' not in session:
        return jsonify(result=1)
    login_user = UserInfo.query.get(session['user_id'])
    if action == 1:  # 关注
        login_user.follow_user.append(follow_user)
        # 处理2：粉丝量+1
        follow_user.follow_count += 1
    else:  # 取消关注
        login_user.follow_user.remove(follow_user)
        # 处理2：粉丝量-1
        follow_user.follow_count -= 1
    # 提交到数据库
    db.session.commit()

    return jsonify(result=2, follow_count=follow_user.follow_count)


@news_blueprint.route('/user/<int:user_id>')
def other(user_id):
    user = UserInfo.query.get(user_id)
    return render_template('news/other.html', user=user)
