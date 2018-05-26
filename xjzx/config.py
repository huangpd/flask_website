class Config(object):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@localhost:3306/xjzx9'
    SQLALCHEMY_TRACK_MODIFICATIONS = True


# 进入开发模式下就把调试打开
class DevelopConfig(Config):
    DEBUG = True
