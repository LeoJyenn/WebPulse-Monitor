import os
from dotenv import load_dotenv

# 定位项目根目录
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) # 获取webpulse_monitor的根目录

# 加载 .env 文件中的环境变量
# 通常 .env 文件应该与 config.py 在同一级目录，或者在基于 basedir 的可预测位置
# 如果 .env 在项目根目录 (与 run.py 同级):
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """
    基础配置类，所有环境的通用配置。
    具体的配置项从环境变量中加载，如果环境变量未设置，则提供一个备用值（主要用于开发）。
    """

    # Flask 应用密钥，极其重要，用于会话加密、CSRF保护等
    # 务必在 .env 文件中设置一个强随机值替换掉备用值
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-bad-default-secret-key-pls-change'

    # 数据库配置
    # 默认使用SQLite，数据库文件将存储在项目根目录下的 instance/app.db
    # 'instance/' 文件夹会在 app/__init__.py 中确保其存在
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    
    # 关闭 Flask-SQLAlchemy 的事件通知系统，如果不使用可以节省资源
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # APScheduler 配置 (可选)
    # 如果需要通过Flask API与调度器交互，可以启用此项
    SCHEDULER_API_ENABLED = os.environ.get('SCHEDULER_API_ENABLED', 'True').lower() in ['true', '1', 't']

    # 日志配置 (示例，可以根据需要扩展)
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()


# 可以为不同环境创建不同的配置类，例如：
# class DevelopmentConfig(Config):
#     DEBUG = True
#     SQLALCHEMY_ECHO = True # 打印SQL语句，用于调试

# class ProductionConfig(Config):
#     DEBUG = False
#     # 生产环境可能需要更严格的日志配置等

# class TestingConfig(Config):
#     TESTING = True
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:' # 测试时使用内存数据库
