from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config # 从项目根目录的 config.py 导入配置
import os
import logging

# 初始化核心扩展，但不立即绑定到应用实例
# 这些实例将在应用工厂函数中绑定
db = SQLAlchemy()
migrate = Migrate()
scheduler = BackgroundScheduler(daemon=True, timezone="UTC") # 设置后台运行和UTC时区

# 配置日志记录
# 您可以根据需要调整日志级别和格式
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper(), # 从环境变量或默认为INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__) # 获取当前模块的logger实例

def create_app(config_class=Config):
    """
    应用工厂函数，用于创建和配置Flask应用实例。
    :param config_class: 配置类，默认为根目录下的 config.py 中定义的 Config 类。
    :return: 配置好的Flask应用实例。
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # 从配置对象加载配置
    app.config.from_object(config_class)
    logger.info(f"应用配置已从 {config_class.__name__} 加载。")
    logger.info(f"当前FLASK_ENV: {app.config.get('ENV')}") # ENV 是 FLASK_ENV 转换后的Flask内部变量
    logger.info(f"当前DEBUG模式: {app.config.get('DEBUG')}")

    # 确保实例文件夹存在 (用于存放SQLite数据库等)
    try:
        if not os.path.exists(app.instance_path):
            os.makedirs(app.instance_path)
            logger.info(f"实例文件夹已创建: {app.instance_path}")
    except OSError as e:
        logger.error(f"创建实例文件夹 {app.instance_path} 失败: {e}")
        # 根据需要，这里可以决定是否抛出异常使应用停止

    # 初始化Flask扩展
    db.init_app(app)
    logger.info("数据库(SQLAlchemy)已初始化。")
    migrate.init_app(app, db)
    logger.info("数据库迁移(Migrate)已初始化。")

    # 导入并注册蓝本 (Blueprints)
    # 蓝本用于组织应用的路由，使代码更模块化
    # 需要在扩展初始化之后，模型定义之前或同时导入（确保模型能被migrate感知）
    from app import routes # 导入 routes 模块 (app/routes.py)
    app.register_blueprint(routes.bp) # 注册在 routes.py 中定义的蓝本 bp
    logger.info("路由蓝本已注册。")

    # 导入模型，确保它们在数据库创建/迁移时被识别
    # 尽管在 run.py 中也导入了，但在这里确保应用上下文内模型被知晓是好的做法
    from app import models 

    # 启动后台调度器 (APScheduler)
    # 确保只在主进程中启动调度器，防止在Flask重载时启动多个实例 (某些情况下)
    # 对于生产环境，通常Gunicorn的worker模型能较好地处理这个问题
    # 但在开发环境下，FLASK_ENV=development 且 DEBUG=True 时，Flask会使用两个进程 (reloader 和 worker)
    if not scheduler.running:
        from app.scheduler_jobs import schedule_all_checks # 导入调度任务的函数
        
        # 使用 with app.app_context() 来确保在调度任务函数内部可以访问数据库和应用配置
        with app.app_context():
            schedule_all_checks(app, scheduler) # 将应用实例和调度器实例传递给任务安排函数
        
        try:
            scheduler.start()
            logger.info("后台调度器(APScheduler)已启动，并已安排监控任务。")
        except (KeyboardInterrupt, SystemExit):
            # 在应用退出时优雅地关闭调度器 (虽然daemon=True会在主程序退出时自动退出)
            scheduler.shutdown()
            logger.info("后台调度器已关闭。")
        except Exception as e:
            logger.error(f"启动后台调度器失败: {e}")
    else:
        logger.info("后台调度器已在运行中。")

    logger.info("WebPulse Monitor 应用实例创建完成。")
    return app
