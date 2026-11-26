from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import css_inline
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings


TEMPLATES = {
    "PASSWORD_RESET_REQUESTED": ("Reset your Ferti+ password", "password_reset_requested"),
    "PASSWORD_CHANGED": ("Your Ferti+ password was changed", "password_changed"),
    "LOGIN_FAILED_ALERT": ("Unsuccessful sign-in attempts on your Ferti+ account", "login_failed_alert"),
    "ONBOARDING_APPROVED": ("Welcome to Ferti+: your shop is approved", "onboarding_approved"),
}


class Renderer:
    def __init__(self):
        template_dir = Path(__file__).resolve().parents[1] / "templates"
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def render(self, template: str, locale: str, data: dict, recipient_name: str | None = None) -> tuple[str, str, str]:
        subject, base_name = TEMPLATES[template]
        locale = locale if locale in ("en", "te", "hi") else "en"
        html_name = f"{locale}/{base_name}.html.j2"
        text_name = f"{locale}/{base_name}.txt.j2"
        try:
            self.env.loader.get_source(self.env, html_name)
        except Exception:
            html_name = f"en/{base_name}.html.j2"
            text_name = f"en/{base_name}.txt.j2"
        subject_template = f"{locale}/{base_name}.subject.j2"
        try:
            self.env.loader.get_source(self.env, subject_template)
        except Exception:
            subject_template = f"en/{base_name}.subject.j2"
        context = dict(data)
        context.setdefault("supportEmail", settings.SUPPORT_EMAIL)
        context["recipientName"] = recipient_name
        rendered_html = self.env.get_template(html_name).render(**context)
        rendered_html = css_inline.inline(rendered_html)
        rendered_text = self.env.get_template(text_name).render(**context)
        rendered_subject = self.env.get_template(subject_template).render(**context).strip()
        return rendered_subject or subject, rendered_html, rendered_text

    def build_mime(self, from_name: str, from_address: str, reply_to: str, to_email: str, to_name: str | None,
                   subject: str, html: str, text: str) -> EmailMessage:
        message = EmailMessage()
        message["From"] = f"{from_name} <{from_address}>"
        message["To"] = f"{to_name} <{to_email}>" if to_name else to_email
        message["Reply-To"] = reply_to
        message["Subject"] = subject
        message["Date"] = datetime.now().astimezone()
        message.set_content(text)
        message.add_alternative(html, subtype="html")
        return message
