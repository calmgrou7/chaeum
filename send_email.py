"""
send_email.py - SMTP 이메일 발송 모듈

Gmail, Outlook, 커스텀 SMTP 서버를 지원하며
TLS/SSL, 개별 수신자 맞춤화, 부분 실패 처리를 지원합니다.
"""

from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SMTPConfig:
    """SMTP 서버 연결 설정."""

    host: str
    port: int
    user: str
    password: str
    from_address: str
    use_tls: bool = True   # STARTTLS (port 587)
    use_ssl: bool = False  # SSL/TLS  (port 465)
    timeout: int = 30


@dataclass
class EmailMessage:
    """발송할 이메일 메시지 데이터."""

    to_address: str
    subject: str
    html_body: str
    plain_body: str = ""
    cc: list[str] = field(default_factory=list)


@dataclass
class SendResult:
    """단일 이메일 발송 결과."""

    to_address: str
    success: bool
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_mime(config: SMTPConfig, message: EmailMessage) -> MIMEMultipart:
    """MIME 메시지 객체를 생성합니다."""
    mime = MIMEMultipart("alternative")
    mime["Subject"] = message.subject
    mime["From"] = config.from_address
    mime["To"] = message.to_address
    if message.cc:
        mime["Cc"] = ", ".join(message.cc)

    # Plain-text fallback
    if message.plain_body:
        mime.attach(MIMEText(message.plain_body, "plain", "utf-8"))

    # HTML body (preferred)
    mime.attach(MIMEText(message.html_body, "html", "utf-8"))
    return mime


def _get_recipients(message: EmailMessage) -> list[str]:
    """수신자 주소 목록을 반환합니다 (To + Cc)."""
    recipients = [message.to_address]
    if message.cc:
        recipients.extend(message.cc)
    return recipients


# ---------------------------------------------------------------------------
# Core send functions
# ---------------------------------------------------------------------------


def _send_via_starttls(config: SMTPConfig, message: EmailMessage) -> None:
    """STARTTLS(포트 587)를 사용하여 이메일을 발송합니다."""
    mime = _build_mime(config, message)
    context = ssl.create_default_context()

    with smtplib.SMTP(config.host, config.port, timeout=config.timeout) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(config.user, config.password)
        server.sendmail(
            config.from_address,
            _get_recipients(message),
            mime.as_string(),
        )


def _send_via_ssl(config: SMTPConfig, message: EmailMessage) -> None:
    """SSL/TLS(포트 465)를 사용하여 이메일을 발송합니다."""
    mime = _build_mime(config, message)
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(config.host, config.port, context=context, timeout=config.timeout) as server:
        server.login(config.user, config.password)
        server.sendmail(
            config.from_address,
            _get_recipients(message),
            mime.as_string(),
        )


def _send_plain(config: SMTPConfig, message: EmailMessage) -> None:
    """암호화 없이 이메일을 발송합니다 (개발/테스트 환경용)."""
    mime = _build_mime(config, message)

    with smtplib.SMTP(config.host, config.port, timeout=config.timeout) as server:
        server.ehlo()
        if config.user and config.password:
            server.login(config.user, config.password)
        server.sendmail(
            config.from_address,
            _get_recipients(message),
            mime.as_string(),
        )


def send_single(config: SMTPConfig, message: EmailMessage, dry_run: bool = False) -> SendResult:
    """단일 이메일을 발송하고 결과를 반환합니다.

    Args:
        config:  SMTP 서버 설정.
        message: 발송할 이메일 정보.
        dry_run: True이면 실제 발송 없이 성공으로 처리합니다.

    Returns:
        SendResult 객체 (성공/실패 여부 포함).
    """
    if dry_run:
        return SendResult(to_address=message.to_address, success=True, error=None)

    try:
        if config.use_ssl:
            _send_via_ssl(config, message)
        elif config.use_tls:
            _send_via_starttls(config, message)
        else:
            _send_plain(config, message)
        return SendResult(to_address=message.to_address, success=True)
    except smtplib.SMTPAuthenticationError as exc:
        return SendResult(
            to_address=message.to_address,
            success=False,
            error=f"인증 실패: {exc}",
        )
    except smtplib.SMTPRecipientsRefused as exc:
        return SendResult(
            to_address=message.to_address,
            success=False,
            error=f"수신자 거부: {exc}",
        )
    except smtplib.SMTPException as exc:
        return SendResult(
            to_address=message.to_address,
            success=False,
            error=f"SMTP 오류: {exc}",
        )
    except OSError as exc:
        return SendResult(
            to_address=message.to_address,
            success=False,
            error=f"네트워크 오류: {exc}",
        )


def send_bulk(
    config: SMTPConfig,
    messages: list[EmailMessage],
    dry_run: bool = False,
    progress_callback=None,
) -> list[SendResult]:
    """여러 이메일을 순차적으로 발송합니다.

    한 건이 실패해도 나머지 발송을 계속 진행합니다.

    Args:
        config:            SMTP 서버 설정.
        messages:          발송할 EmailMessage 목록.
        dry_run:           True이면 실제 발송을 건너뜁니다.
        progress_callback: 각 발송 후 호출되는 콜백 (result, index, total).

    Returns:
        각 메시지에 대한 SendResult 목록.
    """
    results: list[SendResult] = []
    total = len(messages)

    for idx, message in enumerate(messages, start=1):
        result = send_single(config, message, dry_run=dry_run)
        results.append(result)

        if progress_callback:
            progress_callback(result, idx, total)

    return results


# ---------------------------------------------------------------------------
# Preset configs
# ---------------------------------------------------------------------------


def gmail_config(user: str, password: str, from_address: str = "") -> SMTPConfig:
    """Gmail SMTP 설정을 반환합니다 (앱 비밀번호 필요)."""
    return SMTPConfig(
        host="smtp.gmail.com",
        port=587,
        user=user,
        password=password,
        from_address=from_address or user,
        use_tls=True,
        use_ssl=False,
    )


def outlook_config(user: str, password: str, from_address: str = "") -> SMTPConfig:
    """Outlook/Hotmail SMTP 설정을 반환합니다."""
    return SMTPConfig(
        host="smtp-mail.outlook.com",
        port=587,
        user=user,
        password=password,
        from_address=from_address or user,
        use_tls=True,
        use_ssl=False,
    )


def naver_config(user: str, password: str, from_address: str = "") -> SMTPConfig:
    """Naver 메일 SMTP 설정을 반환합니다."""
    return SMTPConfig(
        host="smtp.naver.com",
        port=587,
        user=user,
        password=password,
        from_address=from_address or user,
        use_tls=True,
        use_ssl=False,
    )
