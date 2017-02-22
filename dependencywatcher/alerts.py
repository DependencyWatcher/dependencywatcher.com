#
# Copyright (c) 2015 DependencyWatcher
# All Rights Reserved.
# 

from dependencywatcher.version import Version
from dependencywatcher.license import License
from dependencywatcher.website.model import Alert, get_or_create, create_if_absent
from dependencywatcher.website.webapp import db, app

class AlertsGenerator(object):

    def _fix_alert(self, type, reference):
        alert = Alert.query.filter_by(type=type, reference_id=reference.id).first()
        if alert is not None:
            alert.fixed = True

    def generate_license_alerts(self, prev_info, dependency):
        """ Generate alerts for updated licenses """
        if dependency.license is not None and "license" in prev_info:
            if License(prev_info["license"]).normalized != dependency.license.normalized:
                bad_license = not License(dependency.license.name).is_valid_for_commercial_use()

                for reference in dependency.references:
                    create_if_absent(Alert, type=Alert.NEW_LICENSE, reference_id=reference.id)
                
                    if reference.repository.private:
                        if bad_license:
                            create_if_absent(Alert, type=Alert.BAD_LICENSE, reference_id=reference.id)
                        else:
                            self._fix_alert(Alert.BAD_LICENSE, reference)

    def generate_version_alerts(self, prev_info, dependency):
        """ Generate alerts for updated version """
        prev_version = Version(prev_info["version"]) if "version" in prev_info else None
        prev_stable_version = Version(prev_info["stable_version"]) if "stable_version" in prev_info else prev_version

        new_last_version = Version(dependency.version)
        new_stable_version = Version(dependency.stable_version) if dependency.stable_version else new_last_version

        for reference in dependency.references:
            ref_version = Version(reference.version)

            check_last = reference.repository.user.settings.unstable_vers
            new_compare_version = new_last_version if check_last else new_stable_version
            if new_compare_version.is_greater(ref_version):

                alert = get_or_create(Alert, type=Alert.NEW_VERSION, reference_id=reference.id)
                if alert is not None:
                    prev_compare_version = prev_version if check_last else prev_stable_version
                    app.logger.debug("Generating alert for %s new version: %s (reference version: %s, old version: %s)" \
                            % (alert.__dict__, new_compare_version, ref_version, prev_compare_version))
                    if prev_compare_version is not None and new_compare_version.is_greater(prev_compare_version):
                            alert.sent = False

                    alert.release_type = new_compare_version.get_release_type(ref_version)
                    alert.fixed = False
            else:
                self._fix_alert(Alert.NEW_VERSION, reference)

    def generate(self, prev_info, dependency):
        self.generate_version_alerts(prev_info, dependency)
        self.generate_license_alerts(prev_info, dependency)

