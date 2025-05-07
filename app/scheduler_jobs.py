import requests
from datetime import datetime, timezone # 确保使用带时区的datetime
from app import db, logger # 从 app/__init__.py 中导入 db 实例和预配置的 logger
from app.models import MonitoredTarget, CheckLog
import time

def perform_check(app_context, target_id):
    """
    对给定的 target_id 执行一次状态检查。
    这个函数会被 APScheduler 定时调用。

    :param app_context: Flask应用的上下文，确保数据库等操作可以在调度任务中正确执行。
    :param target_id: 需要检查的 MonitoredTarget 的 ID。
    """
    with app_context: # 进入Flask应用上下文
        target = db.session.get(MonitoredTarget, target_id) # 使用 SQLAlchemy 2.0+ 的 get 方法通过主键获取

        if not target:
            logger.warning(f"调度任务：尝试检查一个不存在的目标 (ID: {target_id})，任务可能已过时。")
            return  # 目标不存在，直接返回

        if not target.is_active:
            logger.info(f"调度任务：目标 '{target.name}' (ID: {target.id}) 当前未激活，跳过检查。")
            return # 目标未激活，跳过

        logger.info(f"调度任务：开始检查目标 '{target.name}' (URL: {target.url})")
        
        status_text = 'PENDING' # 初始状态
        status_code = None
        response_time_ms = None
        details = ''
        check_timestamp = datetime.now(timezone.utc) # 记录检查开始的时间戳 (UTC)

        try:
            start_time = time.perf_counter() # 使用更精确的计时器
            # 发送HTTP GET请求，设置超时和User-Agent
            response = requests.get(target.url, timeout=10, headers={'User-Agent': f'WebPulseMonitor/1.0 ({target.name})'})
            end_time = time.perf_counter()
            response_time_ms = round((end_time - start_time) * 1000, 2) # 计算响应时间，保留两位小数

            status_code = response.status_code
            # 通常认为 2xx 和 3xx 系列的状态码表示服务是可访问的 (UP)
            if 200 <= status_code < 400:
                status_text = 'UP'
                logger.info(f"目标 '{target.name}' 状态: UP, 状态码: {status_code}, 响应时间: {response_time_ms}ms")
            else: # 4xx 和 5xx 系列的状态码通常表示服务有问题 (DOWN)
                status_text = 'DOWN'
                details = f"HTTP 错误状态码: {status_code} - {response.reason}"
                logger.warning(f"目标 '{target.name}' 状态: DOWN, 状态码: {status_code}, 响应时间: {response_time_ms}ms. 详情: {details}")

        except requests.exceptions.Timeout:
            status_text = 'DOWN'
            details = "请求超时 (超过10秒)。"
            logger.warning(f"目标 '{target.name}' (URL: {target.url}) 请求超时。")
        except requests.exceptions.ConnectionError as e:
            status_text = 'DOWN'
            details = f"连接错误 (无法解析主机或连接到服务器): {e.__class__.__name__}"
            logger.warning(f"目标 '{target.name}' (URL: {target.url}) 连接错误: {details}")
        except requests.exceptions.RequestException as e: # 捕获其他所有 'requests' 库可能抛出的异常
            status_text = 'ERROR'
            details = f"请求发生未知错误: {str(e)} (类型: {e.__class__.__name__})"
            logger.error(f"检查目标 '{target.name}' (URL: {target.url}) 时发生 'requests' 库相关错误: {e}")
        except Exception as e: # 捕获其他所有预料之外的异常
            status_text = 'ERROR'
            details = f"执行检查时发生未知系统错误: {str(e)} (类型: {e.__class__.__name__})"
            logger.critical(f"检查目标 '{target.name}' (URL: {target.url}) 时发生严重未知错误: {e}", exc_info=True)


        # 更新 MonitoredTarget 表中的 last_checked_on 字段
        target.last_checked_on = check_timestamp
        
        # 创建并保存检查日志条目
        log_entry = CheckLog(
            target_id=target.id,
            timestamp=check_timestamp, # 使用检查开始时的时间戳
            status_code=status_code,
            status_text=status_text,
            response_time_ms=response_time_ms,
            details=details
        )
        db.session.add(log_entry)
        
        try:
            db.session.commit() # 提交会话，将日志和target的更新保存到数据库
            logger.debug(f"为目标 '{target.name}' (ID: {target.id}) 成功保存了检查日志和更新了last_checked_on。")
        except Exception as e:
            db.session.rollback() # 如果提交失败，回滚事务
            logger.error(f"为目标 '{target.name}' (ID: {target.id}) 保存检查日志时数据库提交失败: {e}", exc_info=True)


def schedule_all_checks(app, scheduler_instance):
    """
    为数据库中所有当前激活的监控目标安排或更新APScheduler的检查任务。
    这个函数会在应用启动时被调用 (在 app/__init__.py 中的 create_app 工厂函数里)。

    :param app: 当前的Flask应用实例。
    :param scheduler_instance: APScheduler的实例。
    """
    with app.app_context(): # 确保在应用上下文中执行数据库查询
        active_targets = MonitoredTarget.query.filter_by(is_active=True).all()
        logger.info(f"发现 {len(active_targets)} 个激活的监控目标需要安排/更新调度任务。")
        
        # 获取当前所有已调度的任务ID，方便清理不再需要的任务
        # scheduled_job_ids = {job.id for job in scheduler_instance.get_jobs()}
        # current_target_job_ids = set()

        for target in active_targets:
            job_id = f'check_target_{target.id}' # 为每个目标创建一个唯一的job ID
            # current_target_job_ids.add(job_id)

            # 检查任务是否已存在，如果存在且配置（如间隔）有变，则更新它
            # APScheduler的 add_job 若设置了 replace_existing=True, 会自动处理更新
            try:
                scheduler_instance.add_job(
                    func=perform_check, # 要执行的函数
                    trigger='interval', # 触发器类型：间隔执行
                    seconds=target.check_interval_seconds, # 执行间隔，从数据库读取
                    args=[app.app_context(), target.id], # 传递给 perform_check 的参数 (应用上下文, 目标ID)
                    id=job_id, # 任务的唯一ID
                    name=f"Check {target.name} ({target.url})", # 任务的可读名称
                    replace_existing=True, # 如果同ID的任务已存在，则替换它
                    misfire_grace_time=60 # 如果任务错过了执行时间点（例如服务器重启），允许60秒的宽限期来执行
                )
                logger.info(f"已为目标 '{target.name}' (ID: {target.id}) 安排/更新了检查任务，每 {target.check_interval_seconds} 秒执行一次。Job ID: {job_id}")
            except Exception as e:
                logger.error(f"为目标 '{target.name}' (ID: {target.id}) 安排任务时发生错误: {e}", exc_info=True)
        
        # (可选的清理逻辑) 清理掉数据库中已不存在或已停用的目标的调度任务
        # for job_id in scheduled_job_ids:
        #     if job_id.startswith('check_target_') and job_id not in current_target_job_ids:
        #         try:
        #             scheduler_instance.remove_job(job_id)
        #             logger.info(f"已清理过时/无效的调度任务: {job_id}")
        #         except Exception as e:
        #             logger.error(f"清理调度任务 {job_id} 时发生错误: {e}", exc_info=True)
