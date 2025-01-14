import logging

log = logging.getLogger(__name__)

def plugin_settings(settings):
    """
    Set of plugin settings used by the Open Edx platform.
    """
    log.info("Tutor Overrides plugin settings loaded")
    settings.OVERRIDE_LTI_PROVIDER = 'tutor_overrides.overrides.override_lti_provider.authenticate_lti_user'
