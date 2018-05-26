from flask import Blueprint

# 首页不加前缀
user_blueprint = Blueprint('user',__name__,url_prefix='/user')
