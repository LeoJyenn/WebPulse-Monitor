# WebPulse Monitor

WebPulse Monitor 是一个简单、可自托管的Web应用程序，旨在监控您的网站和在线服务的正常运行时间及状态。它提供了一个简洁的Web界面，方便您添加、管理和查看被监控目标的状态历史记录。


## ✨ 功能特性

* **网页管理界面**：通过浏览器轻松管理监控目标。
* **添加和移除目标**：动态添加新的URL进行监控，或删除现有目标。
* **状态监控**：定期检查您配置的URL的HTTP状态。
* **状态历史记录**：为每个目标保存状态变更日志。
* **SQLite后端**：使用简单的基于文件的SQLite数据库，易于设置。
* **后台定时任务**：使用APScheduler在后台可靠地执行检查任务。
* **开源**：采用MIT许可证。

## 🛠️ 技术栈

* **后端**：Python 3, Flask
* **数据库**：SQLite (配合 Flask-SQLAlchemy 和 Flask-Migrate)
* **任务调度**：APScheduler
* **前端**：基础 HTML, CSS (使用 Jinja2 模板引擎)
* **WSGI服务器 (部署时使用)**：Gunicorn (推荐)

## 快速开始

以下说明将帮助您在本地计算机上搭建并运行项目副本，以便进行开发和测试。有关如何在实际系统（如VPS）上部署项目的说明，请参阅部署部分。

### 前提条件

* Python 3.8 或更高版本
* `pip` (Python包安装器)
* `git` (版本控制工具)

### 安装步骤 (本地开发环境)

1.  **克隆仓库：**
    ```bash
    git clone [https://github.com/LeoJyenn/webpulse_monitor.git](https://github.com/LeoJyenn/webpulse_monitor.git)
    cd webpulse_monitor
    ```
    *(请确保您已在GitHub上创建了名为 `webpulse_monitor` 的仓库)*

2.  **创建并激活Python虚拟环境：**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Windows系统请使用 `venv\Scripts\activate`
    ```

3.  **安装项目依赖：**
    ```bash
    pip install -r requirements.txt
    ```

4.  **设置环境变量：**
    将 `.env.example` 文件复制为 `.env`，并填写必要的值（尤其是 `SECRET_KEY`）。
    ```bash
    cp .env.example .env
    # 然后用文本编辑器打开 .env 文件，设置一个强壮的 SECRET_KEY
    ```
    `.flaskenv` 文件已预设了 `FLASK_APP` 和 `FLASK_ENV`。

5.  **初始化并迁移数据库：**
    ```bash
    flask db init   # 首次设置项目时只需运行一次
    flask db migrate -m "初始数据库迁移" # 创建迁移脚本
    flask db upgrade  # 将迁移应用到数据库 (创建数据表)
    ```

6.  **运行开发服务器：**
    ```bash
    flask run
    ```
    应用现在应该运行在 `http://127.0.0.1:5000/`。

## 部署到VPS (概念步骤)

1.  确保您的VPS上已安装Python 3.8+、pip和git。
2.  将您的仓库 (`https://github.com/LeoJyenn/webpulse_monitor.git`) 克隆到VPS上。
3.  如上所述，创建虚拟环境并安装依赖。
4.  设置包含生产环境 `SECRET_KEY` 的 `.env` 文件。
5.  运行 `flask db upgrade` 来设置生产数据库。
6.  使用生产级的WSGI服务器（如Gunicorn）来运行应用：
    ```bash
    # 示例：(在激活的虚拟环境和项目根目录下执行)
    # gunicorn --workers 3 --bind 0.0.0.0:8000 run:app
    ```
7.  (推荐) 设置进程管理工具（如 `systemd` 或 `supervisor`）来管理Gunicorn进程（保持运行、开机自启）。
8.  (推荐) 设置反向代理服务器（如 Nginx 或 Apache）来处理入站连接、提供静态文件，以及可选地管理SSL/TLS证书。

## 使用方法

* 在浏览器中打开Web应用。
* 使用“添加新目标”表单来添加您想要监控的URL。
* 主仪表盘将显示所有监控目标的当前状态。
* 点击目标的“查看日志”链接可以查看其状态历史记录。

## 贡献

本项目主要用于演示和个人使用。如果您有任何建议或发现错误，欢迎在 `https://github.com/LeoJyenn/webpulse_monitor/issues` 提交Issue。
*(您可以根据实际情况调整此部分内容)*

## 许可证

本项目采用MIT许可证授权 - 详细信息请参阅 [LICENSE](LICENSE) 文件。

## 致谢
