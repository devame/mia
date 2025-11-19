#!/usr/bin/env python3
"""
Email Notification Module
Sends email notifications for sync results and errors
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import List, Dict, Optional
import json


class EmailNotifier:
    """Handles email notifications for holiday calendar sync operations"""

    def __init__(self, smtp_server: str, smtp_port: int, sender_email: str,
                 sender_password: str, use_tls: bool = True):
        """
        Initialize email notifier

        Args:
            smtp_server: SMTP server address (e.g., smtp.gmail.com)
            smtp_port: SMTP port (e.g., 587 for TLS, 465 for SSL)
            sender_email: Sender email address
            sender_password: Sender email password or app password
            use_tls: Whether to use TLS (default: True)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls

    def send_email(self, recipient_emails: List[str], subject: str,
                   body_html: str, body_text: Optional[str] = None,
                   attachments: Optional[List[str]] = None) -> bool:
        """
        Send an email

        Args:
            recipient_emails: List of recipient email addresses
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body content (optional)
            attachments: List of file paths to attach (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(recipient_emails)
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

            # Add plain text version
            if body_text:
                msg.attach(MIMEText(body_text, 'plain'))

            # Add HTML version
            msg.attach(MIMEText(body_html, 'html'))

            # Add attachments
            if attachments:
                for file_path in attachments:
                    try:
                        with open(file_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition',
                                            f'attachment; filename={file_path.split("/")[-1]}')
                            msg.attach(part)
                    except Exception as e:
                        print(f"Warning: Could not attach file {file_path}: {e}")

            # Send email
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)

            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_sync_report(self, recipient_emails: List[str], sync_results: Dict) -> bool:
        """
        Send synchronization report email

        Args:
            recipient_emails: List of recipient email addresses
            sync_results: Dictionary containing sync results

        Returns:
            True if email sent successfully, False otherwise
        """
        # Extract statistics
        stats = sync_results.get('stats', {})
        errors = sync_results.get('errors', [])
        exchange_results = sync_results.get('exchange_results', [])

        # Determine overall status
        if stats.get('exchanges_failed', 0) == 0 and not errors:
            status = 'SUCCESS'
            status_color = '#28a745'  # Green
        elif stats.get('exchanges_succeeded', 0) > 0:
            status = 'PARTIAL SUCCESS'
            status_color = '#ffc107'  # Yellow
        else:
            status = 'FAILED'
            status_color = '#dc3545'  # Red

        # Build HTML email
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: {status_color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .stats {{ background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
                .stat-item {{ padding: 10px; background: white; border-radius: 4px; }}
                .stat-label {{ font-weight: bold; color: #666; }}
                .stat-value {{ font-size: 24px; color: #007bff; }}
                .error-section {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
                .success-section {{ background-color: #d4edda; border-left: 4px solid #28a745; padding: 15px; margin: 20px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #007bff; color: white; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Exchange Holiday Calendar Sync Report</h1>
                <h2>Status: {status}</h2>
                <p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="content">
                <div class="stats">
                    <h3>Overall Statistics</h3>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-label">Exchanges Processed</div>
                            <div class="stat-value">{stats.get('exchanges_processed', 0)}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Exchanges Succeeded</div>
                            <div class="stat-value">{stats.get('exchanges_succeeded', 0)}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Exchanges Failed</div>
                            <div class="stat-value">{stats.get('exchanges_failed', 0)}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Holidays Added</div>
                            <div class="stat-value">{stats.get('holidays_added', 0)}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Holidays Updated</div>
                            <div class="stat-value">{stats.get('holidays_updated', 0)}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Holidays Unchanged</div>
                            <div class="stat-value">{stats.get('holidays_unchanged', 0)}</div>
                        </div>
                    </div>
                </div>
        """

        # Add exchange results table
        if exchange_results:
            html_body += """
                <h3>Exchange Results</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Exchange</th>
                            <th>ISO Code</th>
                            <th>Status</th>
                            <th>Added</th>
                            <th>Updated</th>
                            <th>Unchanged</th>
                        </tr>
                    </thead>
                    <tbody>
            """

            for result in exchange_results:
                status_icon = '✓' if result.get('success') else '✗'
                row_style = '' if result.get('success') else 'background-color: #f8d7da;'

                html_body += f"""
                        <tr style="{row_style}">
                            <td>{result.get('exchange_name', 'Unknown')}</td>
                            <td>{result.get('iso_code', 'N/A')}</td>
                            <td>{status_icon}</td>
                            <td>{result.get('added', 0)}</td>
                            <td>{result.get('updated', 0)}</td>
                            <td>{result.get('unchanged', 0)}</td>
                        </tr>
                """

            html_body += """
                    </tbody>
                </table>
            """

        # Add errors section
        if errors:
            html_body += """
                <div class="error-section">
                    <h3>Errors Encountered</h3>
                    <ul>
            """

            for error in errors:
                html_body += f"<li>{error}</li>"

            html_body += """
                    </ul>
                </div>
            """

        # Add URL failures section
        url_failures = [r for r in exchange_results if not r.get('url_accessible', True)]
        if url_failures:
            html_body += """
                <div class="error-section">
                    <h3>URL Access Failures</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Exchange</th>
                                <th>URL</th>
                                <th>Error</th>
                                <th>Alternative URL</th>
                            </tr>
                        </thead>
                        <tbody>
            """

            for failure in url_failures:
                alt_url = failure.get('alternative_url', 'Not found')
                html_body += f"""
                        <tr>
                            <td>{failure.get('exchange_name', 'Unknown')}</td>
                            <td><a href="{failure.get('url', '#')}">{failure.get('url', 'N/A')}</a></td>
                            <td>{failure.get('error_message', 'Unknown error')}</td>
                            <td>{alt_url if alt_url != 'Not found' else '<span style="color: red;">Not found</span>'}</td>
                        </tr>
                """

            html_body += """
                    </tbody>
                </table>
            </div>
            """

        html_body += """
            </div>

            <div class="footer">
                <p>This is an automated email from the Exchange Holiday Calendar Sync System.</p>
                <p>Please do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        # Build plain text version
        text_body = f"""
Exchange Holiday Calendar Sync Report
Status: {status}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Overall Statistics:
- Exchanges Processed: {stats.get('exchanges_processed', 0)}
- Exchanges Succeeded: {stats.get('exchanges_succeeded', 0)}
- Exchanges Failed: {stats.get('exchanges_failed', 0)}
- Holidays Added: {stats.get('holidays_added', 0)}
- Holidays Updated: {stats.get('holidays_updated', 0)}
- Holidays Unchanged: {stats.get('holidays_unchanged', 0)}
        """

        if errors:
            text_body += "\n\nErrors Encountered:\n"
            for error in errors:
                text_body += f"- {error}\n"

        # Send email
        subject = f"Holiday Calendar Sync Report - {status} - {datetime.now().strftime('%Y-%m-%d')}"
        return self.send_email(recipient_emails, subject, html_body, text_body)


def load_email_config(config_file: str = 'email_config.json') -> Optional[Dict]:
    """
    Load email configuration from JSON file

    Args:
        config_file: Path to configuration file

    Returns:
        Configuration dictionary or None if not found
    """
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Email configuration file not found: {config_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing email configuration: {e}")
        return None


if __name__ == '__main__':
    # Create example configuration file
    example_config = {
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "sender_email": "your-email@gmail.com",
        "sender_password": "your-app-password",
        "recipient_emails": [
            "recipient1@example.com",
            "recipient2@example.com"
        ],
        "use_tls": True
    }

    with open('email_config.example.json', 'w') as f:
        json.dump(example_config, f, indent=4)

    print("Created example email configuration: email_config.example.json")
    print("Please copy this file to email_config.json and update with your credentials.")
