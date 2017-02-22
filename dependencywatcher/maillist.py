#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from dependencywatcher.db_conf import DBConf
from dependencywatcher.website.webapp import app
import mailchimp

class MailList(object):

	def subscribe(self, email, list_id):

		conf = DBConf.get()

		if conf.mailchimp_api_key is None:
			app.logging.warning("MailChimp API key is not set")
		else:
			api = mailchimp.Mailchimp(conf.mailchimp_api_key)
			try:
				api.lists.subscribe(list_id, {"email": email}, double_optin=False)
			except mailchimp.ListAlreadySubscribedError:
				pass

	def subscribe_to_all(self, email):

		conf = DBConf.get()

		if conf.mailchimp_list_news is not None:
			self.subscribe(email, conf.mailchimp_list_news)

