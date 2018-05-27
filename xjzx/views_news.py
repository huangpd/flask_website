from flask import Blueprint,render_template

# 首页不加前缀
news_blueprint = Blueprint('news',__name__)


@news_blueprint.route('/')
def index():
    return render_template('news/index.html')
