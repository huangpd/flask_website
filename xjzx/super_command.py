from flask import current_app
from flask_script.commands import Command
from models import db, UserInfo
from datetime import datetime
import random

# 自定义创建管理员的命令类，将来添加到manager中
class CreateAdminCommand(Command):
    # 重写run方法，在终端调用时这个方法会被调用
    def run(self):
        # 接受用户输入的账号、密码
        mobile = input('请输入账号：')
        pwd = input('请输入密码：')
        # 验证
        user_exists = UserInfo.query.filter_by(mobile=mobile).count()
        if user_exists > 0:
            print('账号已存在，请重新添加')
            return
            # 如果账号不存在，则添加到表中
        user = UserInfo()
        user.mobile = mobile
        user.password = pwd
        user.isAdmin = True
        # 保存
        db.session.add(user)
        db.session.commit()

        print('创建管理员成功')


class RegisterUserCommand(Command):
    def run(self):
        user_list = []
        for i in range(1000):
            user = UserInfo()
            user.mobile = str(i)
            user.nick_name = str(i)
            user.create_time = datetime(2018,random.randint(1,6),random.randint(1,28))
            user_list.append(user)
        db.session.add_all(user_list)
        db.session.commit()


# 造每小时登陆活跃数，放在redis里
class HourLoginCommand(Command):
    def run(self):
        now=datetime.now()
        key='login%d_%d_%d' % (now.year,now.month,now.day)
        for i in range(8,20):
            current_app.redis_client.hset(key, '%02d:15' % i,random.randint(100,2000))