#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from reportlab.platypus import *
from reportlab.lib.units import inch
from datetime import datetime, timedelta
from dependencywatcher.reports.pdf_report import *

class WeeklyReport(PdfReport):
	def __init__(self, period_start=None, period_end=None, user=None, **kw):
		PdfReport.__init__(self, **kw)
		if period_end is None:
			period_end = datetime.now()
		if period_start is None:
			period_start = period_end - timedelta(days=7)
		self.period_start = period_start
		self.period_end = period_end
		self.user = user

	def _get_diff(self, field):
		value = getattr(self.user.stats, field)
		if self.user.stats_prev is not None:
			value = value - getattr(self.user.stats_prev, field)
		return value if value > 0 else 0

	def append(self, story):
		story.append(Spacer(0, 0.25 * inch))
		story.append(LogoWithTitle("Weekly Report"))
		story.append(Paragraph("%s - %s" % (self.period_start.strftime("%d %B"), self.period_end.strftime("%d %B, %Y")), Styles.Period))
		story.append(Spacer(0, 0.15 * inch))
		story.append(HorizontalLine())

		story.append(Header("New Issues vs. Fixed"))
		story.append(PieChart([
			("Outdated Versions", self._get_diff("oldver")),
			("Licensing Issues", self._get_diff("licissues")),
			("Fixed Issues", self._get_diff("alerts_f"))
		]))

		story.append(Header("New Releases"))
		story.append(PieChart([
			("Major", self._get_diff("oldver_maj")),
			("Minor", self._get_diff("oldver_min")),
			("BugFix", self._get_diff("oldver_bug"))
		]))

