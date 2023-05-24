from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentEndpoints(object):
    """All available Hubble Payment API endpoints."""

    get_user_token: str = 'user.m2m.impersonateUser'
    get_summary: str = 'payment.app.getSummary'
    verify: str = 'payment.app.verify'
    get_authorized_jwt: str = 'payment.app.getAuthorizedJWT'
    report_usage: str = 'payment.app.reportUsage'
