from app import db # 从 app/__init__.py 中导入 SQLAlchemy 数据库实例
from datetime import datetime, timezone # 确保使用带时区的datetime对象

class MonitoredTarget(db.Model):
    """
    代表一个被监控的网站或服务目标。
    """
    __tablename__ = 'monitored_target' # 明确指定表名

    id = db.Column(db.Integer, primary_key=True) # 主键ID
    name = db.Column(db.String(100), nullable=False, index=True) # 用户定义的易记名称，加索引方便查询
    url = db.Column(db.String(512), nullable=False, unique=True, index=True) # 被监控的URL，必须唯一，加索引
    check_interval_seconds = db.Column(db.Integer, default=300, nullable=False) # 检查间隔，单位秒，默认5分钟
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True) # 是否激活对此目标的监控，加索引
    added_on = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc)) # 添加时间，使用带时区的UTC时间
    last_checked_on = db.Column(db.DateTime, nullable=True) # 上次检查的时间戳

    # 定义与 CheckLog 模型的一对多关系
    # 'check_logs' 属性可以用来访问与此目标关联的所有日志记录
    # backref='target' 会在 CheckLog 模型中创建一个隐式的 'target' 属性，指向关联的 MonitoredTarget 对象
    # lazy='dynamic' 表示关联的日志不会立即加载，而是返回一个查询对象，可以进一步过滤或排序
    # cascade="all, delete-orphan" 表示当删除一个 MonitoredTarget 时，所有关联的 CheckLog 也会被删除
    check_logs = db.relationship('CheckLog', backref='target', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        # 定义对象的字符串表示形式，方便调试
        return f'<MonitoredTarget id={self.id} name="{self.name}" url="{self.url}" active={self.is_active}>'

class CheckLog(db.Model):
    """
    记录每一次对监控目标的检查结果。
    """
    __tablename__ = 'check_log' # 明确指定表名

    id = db.Column(db.Integer, primary_key=True) # 主键ID
    
    # 外键，关联到 MonitoredTarget 表的 id 字段
    # index=True 可以加快基于 target_id 的查询
    target_id = db.Column(db.Integer, db.ForeignKey('monitored_target.id', name='fk_checklog_target_id'), nullable=False, index=True)
    
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True) # 检查发生的时间戳，使用带时区的UTC时间，加索引
    status_code = db.Column(db.Integer, nullable=True) # HTTP响应状态码，例如 200, 404, 500
    status_text = db.Column(db.String(50), nullable=False) # 状态描述，例如 'UP', 'DOWN', 'ERROR', 'PENDING'
    response_time_ms = db.Column(db.Float, nullable=True) # 响应时间，单位毫秒
    details = db.Column(db.Text, nullable=True) # 额外详情，例如错误信息或特定的检查点

    def __repr__(self):
        # 定义对象的字符串表示形式
        return f'<CheckLog id={self.id} target_id={self.target_id} status="{self.status_text}" timestamp="{self.timestamp}">'
