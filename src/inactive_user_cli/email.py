"""邮件通知模块"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

from inactive_user_cli.config import EmailConfig, Config


class EmailNotifier:
    """邮件通知器"""

    def __init__(self, config: EmailConfig):
        self.config = config

    def send_delete_report(
        self,
        total: int,
        success: int,
        failed: int,
        log_file: str,
        records: list[dict],
    ) -> bool:
        """发送删除报告邮件

        Args:
            total: 总删除数
            success: 成功数
            failed: 失败数
            log_file: 日志文件路径
            records: 删除记录列表

        Returns:
            是否发送成功
        """
        if not self.config.enabled:
            return False

        # 构建邮件内容
        subject = f"[{self.config.from_addr}] 删除用户报告 - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"

        # HTML 格式的邮件内容
        html_content = f"""
        <html>
        <body>
        <h2>删除用户操作报告</h2>
        <p><strong>执行时间:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        <p><strong>日志文件:</strong> {log_file}</p>

        <h3>执行结果摘要</h3>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>总删除数</th>
                <th>成功</th>
                <th>失败</th>
                <th>成功率</th>
            </tr>
            <tr>
                <td>{total}</td>
                <td style="color: green;">{success}</td>
                <td style="color: red;">{failed}</td>
                <td>{success/total*100:.1f}%</td>
            </tr>
        </table>
        """

        if records:
            html_content += """
        <h3>详细记录</h3>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>用户名</th>
                <th>用户ID</th>
                <th>邮箱</th>
                <th>状态</th>
                <th>错误信息</th>
            </tr>
        """

            for record in records:
                status_style = "color: green;" if record.get("status") == "success" else "color: red;"
                html_content += f"""
            <tr>
                <td>{record.get('username', '-')}</td>
                <td>{record.get('user_id', '-')}</td>
                <td>{record.get('email', '-')}</td>
                <td style="{status_style}">{record.get('status', '-')}</td>
                <td>{record.get('error', '-')}</td>
            </tr>
        """

            html_content += "</table>"

        html_content += """
        <hr>
        <p style="color: gray; font-size: 12px;">
        此邮件由 hiagent-user-cli 自动发送
        </p>
        </body>
        </html>
        """

        # 纯文本版本（备选）
        text_content = f"""
删除用户操作报告

执行时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC
日志文件: {log_file}

执行结果摘要:
- 总删除数: {total}
- 成功: {success}
- 失败: {failed}
- 成功率: {success/total*100:.1f}%

详细记录:
"""

        for record in records:
            status = record.get("status", "-")
            error = record.get("error", "")
            text_content += f"- {record.get('username', '-')} ({record.get('user_id', '-')}): {status}"
            if error:
                text_content += f" - {error}"
            text_content += "\n"

        # 发送邮件
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.config.from_addr
            msg["To"] = ",".join(self.config.to_addrs)

            # 添加纯文本和 HTML 版本
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            # 连接 SMTP 服务器并发送
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()
                server.login(self.config.smtp_user, self.config.smtp_password)
                server.sendmail(self.config.from_addr, self.config.to_addrs, msg.as_string())

            return True

        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False


def send_delete_notification(
    config: Config,
    total: int,
    success: int,
    failed: int,
    log_file: str,
    records: list[dict],
) -> bool:
    """发送删除通知（如果配置了邮件）

    Args:
        config: 全局配置
        total: 总删除数
        success: 成功数
        failed: 失败数
        log_file: 日志文件路径
        records: 删除记录列表

    Returns:
        是否发送成功
    """
    if not config.email or not config.email.enabled:
        return False

    notifier = EmailNotifier(config.email)
    return notifier.send_delete_report(total, success, failed, log_file, records)