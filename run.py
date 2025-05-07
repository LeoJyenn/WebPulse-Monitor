from app import create_app, db # 从 app 包中导入 create_app 工厂函数和 db 实例
from app.models import MonitoredTarget, CheckLog # 导入模型，确保 Flask-Migrate 能检测到它们
from flask_migrate import Migrate

# 调用工厂函数创建 Flask 应用实例
# create_app() 会加载 config.py 中的配置
app = create_app()

# 初始化 Flask-Migrate
# Migrate 实例需要应用实例和 SQLAlchemy 的 db 实例作为参数
migrate = Migrate(app, db)

# @app.shell_context_processor
# def make_shell_context():
#     """
#     为 flask shell 命令添加额外的上下文变量。
#     这样在 flask shell 中可以直接使用 db, MonitoredTarget, CheckLog 等变量，方便调试。
#     """
#     return {'db': db, 'MonitoredTarget': MonitoredTarget, 'CheckLog': CheckLog}

if __name__ == '__main__':
    # 当直接运行这个脚本时 (python run.py)
    # Flask 的内置开发服务器会启动。
    # host='0.0.0.0' 使服务器可以从网络上的任何IP访问，而不仅仅是本地回环地址 (127.0.0.1)。
    # debug=True (或 FLASK_ENV=development 在 .flaskenv 中设置) 会启用调试模式，
    # 这包括代码更改时自动重载服务器和提供详细的错误页面。
    # 在生产环境中，你应该使用 Gunicorn 或 uWSGI 这样的生产级 WSGI 服务器，而不是 Flask 内置的开发服务器。
    # 端口号也可以在这里指定，例如 app.run(host='0.0.0.0', port=5000, debug=app.config.get('DEBUG', True))
    # 但通常我们通过 .flaskenv 或环境变量来控制 DEBUG 模式。
    
    # 注意：FLASK_APP=run.py 和 FLASK_ENV=development 已经在 .flaskenv 中设置。
    # 所以直接执行 `flask run` 命令会使用这些设置。
    # 直接执行 `python run.py` 也会启动开发服务器，但它可能不会完全遵循 .flaskenv 中的所有设置，
    # 除非你在 app.run() 中显式传递它们。
    # 推荐使用 `flask run` 命令来启动开发服务器。
    
    app.run() # 这里的 host 和 port 可以不指定，Flask 会使用默认值 (127.0.0.1:5000)
              # 如果 .flaskenv 中没有设置 FLASK_DEBUG=1, 默认 debug=False
              # 但因为 FLASK_ENV=development, debug 通常会是 True
