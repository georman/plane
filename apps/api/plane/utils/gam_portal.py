# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.
#
# GAM addition: client portal links. A customer's personal link is a signed
# token carrying the customer id and portal_version; a new link (version + 1)
# makes the old one stop working.

from django.core import signing

from plane.db.models import Customer
from plane.license.utils.gam_brand import web_url

PORTAL_SALT = "gam-client-portal"


def portal_url(customer):
    token = signing.dumps(f"{customer.id}:{customer.portal_version}", salt=PORTAL_SALT)
    return f"{web_url()}/api/gam/portal/{token}/"


def customer_from_token(token):
    try:
        value = signing.loads(token, salt=PORTAL_SALT)
    except signing.BadSignature:
        return None
    customer_id, _, version = str(value).partition(":")
    customer = Customer.objects.filter(pk=customer_id, is_active=True).first()
    if not customer or str(customer.portal_version) != version:
        return None
    return customer
