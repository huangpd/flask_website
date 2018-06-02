from flask import Blueprint, render_template, jsonify
from flask import abort
from flask import request
from flask import session

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
    # 接受页码
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
        count_list=count_list
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
    comment_list = NewsComment.query.filter_by(news_id=news_id).order_by(NewsComment.like_count.desc(),
                                                                         NewsComment.create_time.desc())
    # 把数据转换成字典格式返回给浏览器
    comment_list2 = []
    for comment in comment_list:
        comment_dict = {
            'id': comment.id,
            'like_count': comment.like_count,
            'msg': comment.msg,
            'create_time': comment.create_time,
            # UserInfo中的comments的属性的反向引用
            'nick_name': comment.user.nick_name,
            'avatar': comment.user.avatar_url
        }
        comment_list2.append(comment_dict)
    return jsonify(comment_list=comment_list2)
