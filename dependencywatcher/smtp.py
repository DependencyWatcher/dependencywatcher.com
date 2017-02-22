#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from dependencywatcher.db_conf import DBConf
from dependencywatcher.website.webapp import app
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import smtplib, os

class SMTPMailer(object):
	def send(self, **kwargs):
		conf = DBConf.get()

		if conf.smtp_server is None:
			app.logger.warning("SMTP client is not configured")
		else:
			sender = kwargs.get("from", conf.smtp_from_addr)
			recipients = kwargs.get("to")

			msg = MIMEMultipart("alternative")
			msg["From"] = sender
			msg["Subject"] = kwargs.get("subject")
			msg["To"] = ", ".join(recipients)

			if "text" in kwargs:
				msg.attach(MIMEText(kwargs.get("text"), "plain"))

			if "html" in kwargs:
				msg.attach(MIMEText(kwargs.get("html"), "html"))

			for f in kwargs.get("files", []):
				attachment = MIMEApplication(file(f).read(), _subtype = os.path.splitext(f)[1][1:])
				attachment.add_header("content-disposition", "attachment", filename=("utf-8", "", os.path.basename(f)))
				msg.attach(attachment)

			if kwargs.get("attach_logo", True):
				with open(os.path.join(os.path.dirname(__file__), "website/static/images/logo32.png"), "rb") as f:
					logoImage = MIMEImage(f.read())
					logoImage.add_header("Content-ID", "<logo32>")
					msg.attach(logoImage)

			msg["X-Entity-Ref-ID"] = ""

			server = smtplib.SMTP_SSL(conf.smtp_server) if conf.smtp_use_ssl else smtplib.SMTP(conf.smtp_server)
			if conf.smtp_username is not None and conf.smtp_password is not None:
				server.login(conf.smtp_username, conf.smtp_password)

			server.sendmail(sender, recipients, msg.as_string())
			server.quit()

