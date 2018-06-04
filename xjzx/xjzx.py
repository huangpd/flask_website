from flask_script import Manager
from app import create_app
from config import DevelopConfig

# 生成app对象
app = create_app(DevelopConfig)
manager = Manager(app)

# 数据库连接配置
from models import db

db.init_app(app)

# 　数据库迁移配置
from flask_migrate import Migrate, MigrateCommand

Migrate(app, db)
manager.add_command('db', MigrateCommand)

# 添加拓展的自定义命令
from super_command import CreateAdminCommand,RegisterUserCommand,HourLoginCommand

# 创建管理员
manager.add_command('createadmin', CreateAdminCommand)
# 注册user
manager.add_command('registeruser',RegisterUserCommand)
# 造小时活跃数
manager.add_command('hourlogin',HourLoginCommand)

if __name__ == '__main__':
    manager.run()
