"""
Provides application configuration for Tutor Overrides.
As well as default values for running Tutor Overrides along with functions to
add entries to the Django conf settings needed to run Tutor Overrides.
"""

from django.apps import AppConfig
from edx_django_utils.plugins.constants import (
    PluginURLs, PluginSettings
)
from openedx.core.djangoapps.plugins.constants import (
    ProjectType, SettingsType
)


class TutorOverridesConfig(AppConfig):
    """
    Provides application configuration for Tutor Overrides.
    """

    name = 'tutor_overrides'
    verbose_name = 'tutor_overrides'

    plugin_app = {
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.COMMON: {
                    PluginSettings.RELATIVE_PATH: u'settings.common'
                },
            }
        }
    }
