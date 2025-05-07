from flask import render_template, redirect, url_for, flash, request, current_app
from app import db, scheduler, logger # 从 app/__init__.py 导入实例
from app.models import MonitoredTarget, CheckLog
from app.forms import AddTargetForm, EditTargetForm # 导入表单类
from app.scheduler_jobs import perform_check # 导入手动检查函数
from flask import Blueprint
import time # 用于手动触发检查时生成唯一ID

# 创建一个蓝本(Blueprint)实例，用于组织一组相关的路由
# 'main' 是蓝本的名称，__name__ 是蓝本所在的模块或包的名称
bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    """
    主页/仪表盘路由。
    显示所有监控目标及其最新的状态。
    """
    logger.info(f"用户访问了主页 (IP: {request.remote_addr})")
    try:
        targets = MonitoredTarget.query.order_by(MonitoredTarget.name.asc()).all()
        latest_statuses = {}
        for target in targets:
            # 为每个目标获取最新的日志条目以显示其当前状态
            latest_log = target.check_logs.order_by(CheckLog.timestamp.desc()).first()
            if latest_log:
                latest_statuses[target.id] = {
                    "status_text": latest_log.status_text,
                    "timestamp": latest_log.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC') if latest_log.timestamp else "N/A",
                    "response_time_ms": latest_log.response_time_ms,
                    "status_code": latest_log.status_code
                }
            else:
                latest_statuses[target.id] = {
                    "status_text": "PENDING", # 如果没有日志，则状态为待定
                    "timestamp": "N/A",
                    "response_time_ms": "N/A",
                    "status_code": "N/A"
                }
    except Exception as e:
        logger.error(f"获取监控目标列表时发生错误: {e}", exc_info=True)
        flash('加载监控目标失败，请稍后重试。', 'danger')
        targets = []
        latest_statuses = {}
        
    return render_template('index.html', title='监控仪表盘', targets=targets, latest_statuses=latest_statuses)

@bp.route('/add_target', methods=['GET', 'POST'])
def add_target():
    """
    添加新的监控目标的路由。
    GET请求显示表单，POST请求处理表单提交。
    """
    form = AddTargetForm()
    if form.validate_on_submit(): # WTForms会自动处理CSRF验证
        logger.info(f"用户尝试添加新监控目标: 名称='{form.name.data}', URL='{form.url.data}'")
        try:
            # 检查URL是否已存在
            existing_target_by_url = MonitoredTarget.query.filter_by(url=form.url.data).first()
            if existing_target_by_url:
                flash(f'错误：URL "{form.url.data}" 已经被监控 (名称: {existing_target_by_url.name})。', 'danger')
                logger.warning(f"添加失败，URL '{form.url.data}' 已存在。")
                return render_template('add_target.html', title='添加监控目标', form=form)

            target = MonitoredTarget(
                name=form.name.data,
                url=form.url.data,
                check_interval_seconds=form.check_interval_seconds.data,
                is_active=form.is_active.data
            )
            db.session.add(target)
            db.session.commit() # 先提交以获取target.id
            logger.info(f"新监控目标 '{target.name}' (ID: {target.id}) 已成功添加到数据库。")
            
            # 如果目标是激活的，则安排调度任务并立即执行一次检查
            if target.is_active:
                job_id = f'check_target_{target.id}'
                scheduler.add_job(
                    perform_check,
                    trigger='interval',
                    seconds=target.check_interval_seconds,
                    args=[current_app.app_context(), target.id], # 传递应用上下文和目标ID
                    id=job_id,
                    name=f"Check {target.name}",
                    replace_existing=True
                )
                logger.info(f"已为新目标 '{target.name}' (ID: {target.id}) 安排了定时检查任务。")
                
                # 安排一次立即执行的检查
                immediate_job_id = f'immediate_check_{target.id}_{int(time.time())}'
                scheduler.add_job(perform_check, args=[current_app.app_context(), target.id], id=immediate_job_id, name=f"Immediate check for {target.name}")
                logger.info(f"已为新目标 '{target.name}' (ID: {target.id}) 安排了一次立即检查。")

            flash(f'监控目标 "{target.name}" 添加成功!', 'success')
            return redirect(url_for('main.index')) # 重定向到主页
            
        except Exception as e:
            db.session.rollback() # 如果发生错误，回滚数据库会话
            logger.error(f"添加监控目标 '{form.name.data}' 时发生数据库错误: {e}", exc_info=True)
            flash(f'添加监控目标时发生内部错误，请稍后重试。错误详情: {str(e)}', 'danger')
            
    return render_template('add_target.html', title='添加监控目标', form=form)

@bp.route('/target/<int:target_id>/delete', methods=['POST']) # 只允许POST请求删除
def delete_target(target_id):
    """
    删除指定的监控目标及其关联的调度任务和日志。
    """
    target_to_delete = db.session.get(MonitoredTarget, target_id) # 使用 SQLAlchemy 2.0+ 的 get 方法
    if target_to_delete:
        logger.info(f"用户尝试删除监控目标: '{target_to_delete.name}' (ID: {target_id})")
        try:
            job_id = f'check_target_{target_to_delete.id}'
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)
                logger.info(f"已从调度器中移除目标 '{target_to_delete.name}' (ID: {target_id}) 的任务。")

            # CheckLog 会因为在MonitoredTarget模型中设置的 cascade="all, delete-orphan" 而被一同删除
            db.session.delete(target_to_delete)
            db.session.commit()
            flash(f'监控目标 "{target_to_delete.name}" 已成功删除。', 'success')
            logger.info(f"监控目标 '{target_to_delete.name}' (ID: {target_id}) 已从数据库中删除。")
        except Exception as e:
            db.session.rollback()
            logger.error(f"删除目标 '{target_to_delete.name}' (ID: {target_id}) 时发生错误: {e}", exc_info=True)
            flash(f'删除目标 "{target_to_delete.name}" 时发生内部错误，请稍后重试。', 'danger')
    else:
        flash('错误：未找到要删除的监控目标。', 'warning')
        logger.warning(f"尝试删除一个不存在的目标 (ID: {target_id})。")
        
    return redirect(url_for('main.index'))

@bp.route('/target/<int:target_id>/toggle_active', methods=['POST']) # 只允许POST请求切换状态
def toggle_active(target_id):
    """
    切换指定监控目标的激活/暂停状态。
    """
    target_to_toggle = db.session.get(MonitoredTarget, target_id)
    if target_to_toggle:
        logger.info(f"用户尝试切换目标 '{target_to_toggle.name}' (ID: {target_id}) 的激活状态，当前为: {'激活' if target_to_toggle.is_active else '暂停'}")
        try:
            target_to_toggle.is_active = not target_to_toggle.is_active
            db.session.commit()
            
            job_id = f'check_target_{target_to_toggle.id}'
            if target_to_toggle.is_active:
                # 如果任务不存在或已被移除，则重新添加
                if not scheduler.get_job(job_id): # 避免重复添加
                    scheduler.add_job(
                        perform_check,
                        trigger='interval',
                        seconds=target_to_toggle.check_interval_seconds,
                        args=[current_app.app_context(), target_to_toggle.id],
                        id=job_id,
                        name=f"Check {target_to_toggle.name}",
                        replace_existing=True # 如果之前因为某些原因没删掉，这里会替换
                    )
                flash(f'目标 "{target_to_toggle.name}" 已激活监控。', 'success')
                logger.info(f"目标 '{target_to_toggle.name}' (ID: {target_id}) 已被设置为激活状态，并已安排/确认调度任务。")
            else: # 如果设置为不激活，则移除调度任务
                if scheduler.get_job(job_id):
                    scheduler.remove_job(job_id)
                flash(f'目标 "{target_to_toggle.name}" 已暂停监控。', 'info')
                logger.info(f"目标 '{target_to_toggle.name}' (ID: {target_id}) 已被设置为暂停状态，并已移除调度任务。")
        except Exception as e:
            db.session.rollback()
            logger.error(f"切换目标 '{target_to_toggle.name}' (ID: {target_id}) 激活状态时发生错误: {e}", exc_info=True)
            flash(f'操作失败: {str(e)}', 'danger')
    else:
        flash('错误：未找到指定的监控目标。', 'warning')
        logger.warning(f"尝试切换一个不存在的目标 (ID: {target_id}) 的激活状态。")
        
    return redirect(url_for('main.index'))

@bp.route('/target/<int:target_id>/logs')
@bp.route('/target/<int:target_id>/logs/page/<int:page>')
def target_logs(target_id, page=1):
    """
    显示指定监控目标的历史检查日志，支持分页。
    """
    target = db.session.get(MonitoredTarget, target_id)
    if not target:
        flash('错误：未找到指定的监控目标。', 'warning')
        logger.warning(f"用户尝试查看不存在的目标 (ID: {target_id}) 的日志。")
        return redirect(url_for('main.index'))
    
    logger.info(f"用户正在查看目标 '{target.name}' (ID: {target_id}) 的日志, 第 {page} 页。")
    try:
        # 日志按时间倒序分页显示，每页显示20条 (可配置)
        logs_pagination = CheckLog.query.filter_by(target_id=target.id)\
                                    .order_by(CheckLog.timestamp.desc())\
                                    .paginate(page=page, per_page=20, error_out=False) # error_out=False 防止页码超出时抛出404
        
        if not logs_pagination.items and page > 1: # 如果当前页没有项目且不是第一页，可能用户手动输入了过大的页码
            logger.warning(f"用户尝试访问目标 '{target.name}' 日志的无效页码: {page}。实际总页数: {logs_pagination.pages}")
            return redirect(url_for('main.target_logs', target_id=target.id, page=logs_pagination.pages or 1))

    except Exception as e:
        logger.error(f"获取目标 '{target.name}' (ID: {target_id}) 日志时发生错误: {e}", exc_info=True)
        flash(f'加载日志失败，请稍后重试。', 'danger')
        logs_pagination = None # 或者一个空的Pagination对象

    return render_template('target_logs.html', title=f'"{target.name}" 的监控日志', 
                           target=target, logs_pagination=logs_pagination)

@bp.route('/target/<int:target_id>/run_check_now', methods=['POST']) # 只允许POST请求
def run_check_now(target_id):
    """
    为指定目标手动触发一次立即检查。
    """
    target = db.session.get(MonitoredTarget, target_id)
    if target:
        if target.is_active:
            logger.info(f"用户为目标 '{target.name}' (ID: {target_id}) 手动触发了一次立即检查。")
            try:
                # 使用 add_job 并设置一个唯一的、基于时间的ID来立即执行一次任务
                # 这样可以利用调度器的执行环境和上下文管理
                immediate_job_id = f'manual_check_{target.id}_{int(time.time())}'
                scheduler.add_job(
                    func=perform_check, 
                    args=[current_app.app_context(), target.id], 
                    id=immediate_job_id, 
                    name=f"Manual check for {target.name}",
                    # trigger='date', run_date=datetime.now(timezone.utc) + timedelta(seconds=1) # 另一种立即执行的方式
                    # 或者不指定trigger，APScheduler默认会立即执行一次性任务
                )
                flash(f'已为 "{target.name}" 手动触发了一次检查。请稍后刷新页面查看结果。', 'info')
            except Exception as e:
                logger.error(f"手动为目标 '{target.name}' (ID: {target_id}) 触发检查时发生错误: {e}", exc_info=True)
                flash(f'手动触发检查失败: {str(e)}', 'danger')
        else:
            flash(f'目标 "{target.name}" 当前未激活，无法手动触发检查。', 'warning')
            logger.warning(f"用户尝试为未激活的目标 '{target.name}' (ID: {target_id}) 手动触发检查。")
    else:
        flash('错误：未找到指定的监控目标。', 'warning')
        logger.warning(f"用户尝试为不存在的目标 (ID: {target_id}) 手动触发检查。")
        
    # 重定向回之前的页面，如果获取不到则回到首页
    return redirect(request.referrer or url_for('main.index'))
