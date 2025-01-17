"""
LTI user management functionality. This module reconciles the two identities
that an individual has in the campus LMS platform and on edX.
"""


import random
import string
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction

from common.djangoapps.student.models import UserProfile
from lms.djangoapps.lti_provider.models import LtiUser
from openedx.core.djangoapps.safe_sessions.middleware import mark_user_change_as_expected


def authenticate_lti_user(prev_fn, request, lti_user_id, lti_consumer):
    """
    Determine whether the user specified by the LTI launch has an existing
    account. If not, create a new Django User model and associate it with an
    LtiUser object.

    If the currently logged-in user does not match the user specified by the LTI
    launch, log out the old user and log in the LTI identity.
    """
    lis_email = request.POST.get("lis_person_contact_email_primary")

    try:
        lti_user = LtiUser.objects.get(
            lti_user_id=lti_user_id,
            lti_consumer=lti_consumer
        )
    except LtiUser.DoesNotExist as exc:
        # This is the first time that the user has been here. Create an account.
        if lti_consumer.require_user_account:
            lti_user = create_lti_user(lti_user_id, lti_consumer, lis_email)
        else:
            lti_user = create_lti_user(lti_user_id, lti_consumer, lis_email)
    # authenticate the user
    switch_user(request, lti_user, lti_consumer)



def create_lti_user(lti_user_id, lti_consumer, email=None):
    """
    Generate a new user on the edX platform with a random username and password,
    and associates that account with the LTI identity.
    """
    edx_user = User.objects.filter(email=email).first() if email else None

    if not edx_user:
        created = False
        edx_password = str(uuid.uuid4())
        while not created:
            try:
                edx_user_id = email.split('@')[0] + ''.join(random.choices(string.digits, k=3))
                edx_email = email
                with transaction.atomic():
                    edx_user = User.objects.create_user(
                        username=edx_user_id,
                        password=edx_password,
                        email=edx_email,
                    )
                    # A profile is required if PREVENT_CONCURRENT_LOGINS flag is set.
                    # TODO: We could populate user information from the LTI launch here,
                    # but it's not necessary for our current uses.
                    edx_user_profile = UserProfile(user=edx_user)
                    edx_user_profile.save()
                    created = True
            except IntegrityError:
                # The random edx_user_id wasn't unique. Since 'created' is still
                # False, we will retry with a different random ID.
                pass

    lti_user = LtiUser(
        lti_consumer=lti_consumer,
        lti_user_id=lti_user_id,
        edx_user=edx_user
    )
    lti_user.save()
    return lti_user


def switch_user(request, lti_user, lti_consumer):
    """
    Log out the current user, and log in using the edX identity associated with
    the LTI ID.
    """
    edx_user = authenticate(
        username=lti_user.edx_user.username,
        lti_user_id=lti_user.lti_user_id,
        lti_consumer=lti_consumer
    )
    if not edx_user:
        # This shouldn't happen, since we've created edX accounts for any LTI
        # users by this point, but just in case we can return a 403.
        raise PermissionDenied()
    login(request, edx_user)
    mark_user_change_as_expected(edx_user.id)


def generate_random_edx_username():
    """
    Create a valid random edX user ID. An ID is at most 30 characters long, and
    can contain upper and lowercase letters and numbers.
    :return:
    """
    allowable_chars = string.ascii_letters + string.digits
    username = ''
    for _index in range(30):
        username = username + random.SystemRandom().choice(allowable_chars)
    return username


class LtiBackend:
    """
    A Django authentication backend that authenticates users via LTI. This
    backend will only return a User object if it is associated with an LTI
    identity (i.e. the user was created by the create_lti_user method above).
    """

    def authenticate(self, _request, username=None, lti_user_id=None, lti_consumer=None):
        """
        Try to authenticate a user. This method will return a Django user object
        if a user with the corresponding username exists in the database, and
        if a record that links that user with an LTI user_id field exists in
        the LtiUser collection.

        If such a user is not found, the method returns None (in line with the
        authentication backend specification).
        """
        try:
            edx_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        try:
            LtiUser.objects.get(
                edx_user_id=edx_user.id,
                lti_user_id=lti_user_id,
                lti_consumer=lti_consumer
            )
        except LtiUser.DoesNotExist:
            return None
        return edx_user

    def get_user(self, user_id):
        """
        Return the User object for a user that has already been authenticated by
        this backend.
        """
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
