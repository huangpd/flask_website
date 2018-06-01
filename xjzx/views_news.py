from flask import Blueprint, render_template, jsonify
from flask import request
from flask import session

from models import db, NewsCategory, UserInfo, NewsInfo

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
    category_id = int(request.args.get('category','0'))

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
