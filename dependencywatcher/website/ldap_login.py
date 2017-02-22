#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from dependencywatcher.db_conf import DBConf
from dependencywatcher.website.webapp import app, db
from dependencywatcher.website.model import User
import ldap

class LDAP_Login(object):
	def _reformat_result(self, result):
		if result is not None and len(result) > 0:
			newres = {}
			for k, v in result[0][1].iteritems():
				if isinstance(v, list):
					newres[k] = None if len(v) == 0 else v[0]
				else:
					newres[k] = v
			return newres
		return None

	def find_or_create_user(self, ldap_result):
		user = None
		try:
			user = User.query.filter_by(email=ldap_result["mail"]).first()
			if not user is None:
				user.activate()
				user.purge_repositories()
			else:
				user = User()
				user.email = ldap_result["mail"]
				if "name" in ldap_result:
					user.name = ldap_result["name"]
				elif "displayName" in ldap_result:
					user.name = ldap_result["displayName"]

				avatar = None
				if "jpegPhoto" in ldap_result:
					avatar = ldap_result["jpegPhoto"]
				elif "thumbnailPhoto" in ldap_result:
					avatar = ldap_result["thumbnailPhoto"]
				if avatar is None:
					user.find_avatar()
				else:
					pass # XXX - implement storing avatar

				db.session.add(user)
				user.perform_new_user_actions()

			user.is_ldap = True
			db.session.commit()
		except KeyError:
			pass
		return user

	def login(self, email, password):
		conf = DBConf.get()
		email = email.encode("utf-8")
		password = password.encode("utf-8")
		try:
			conn = ldap.initialize(conf.ldap_url)
			conn.set_option(ldap.OPT_REFERRALS, 0)
			conn.bind_s(email, password)
			try:
				result = conn.search_s(conf.ldap_basedn, ldap.SCOPE_SUBTREE, u"mail=%s" % email, [
					"displayName", "name", "mail", "jpegPhoto", "thumbnailPhoto"
				])
				result = self._reformat_result(result)
				if result is not None:
					return self.find_or_create_user(result)
			finally:
				conn.unbind_s()
		except ldap.LDAPError as e:
			pass
		return None

