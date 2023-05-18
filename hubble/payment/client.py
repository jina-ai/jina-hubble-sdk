import uuid

from hubble.utils.jwt_parser import validate_jwt

from .base import PaymentBaseClient
from .endpoints import PaymentEndpoints


class PaymentClient(PaymentBaseClient):
    def get_user_token(self, user_id) -> dict:
        return self.handle_request(
            url=self._base_url + PaymentEndpoints.get_user_token,
            data={'userId': user_id},
        )

    def get_authorized_jwt(
        self, user_token: str, expiration_seconds: int = 15 * 60 * 1000
    ) -> dict:
        """Create a payment authorized JWT for user.

        :param user_id: The _id of the user.
        :param expiration_seconds: Number of seconds until the JWT expires.
        :returns: Object.
        """
        return self.handle_request(
            url=self._base_url + PaymentEndpoints.get_authorized_jwt,
            data={'token': user_token, 'ttl': expiration_seconds},
        )

    def verify_authorized_jwt(self, token: str) -> bool:
        """Verify if a token is a payment authorized JWT

        :param token: User token.
        :returns: Boolean (true if payment authorized, false otherwise)
        """

        try:
            decoded = validate_jwt(token)
            is_authorized = decoded.get('paymentAuthorized', False)
            return is_authorized
        except Exception:
            return False

    def get_summary(self, token: str, app_id: str) -> object:
        """Get a list of a user's subscriptions and consumption for a given app.

        :param token: User token.
        :param app_id: ID of the application.
        :returns: Object
        """

        return self.handle_request(
            url=self._base_url + PaymentEndpoints.get_summary,
            data={'token': token, 'internalAppId': app_id},
        )

    def report_usage(
        self,
        token: str,
        app_id: str,
        product_id: str,
        credits: int,
        meta: dict = {},
    ) -> object:

        """Report usage for a given app using the deprecated format.

        :param token: User token.
        :param app_id: ID of the application.
        :param product_id: ID of the product.
        :returns: Object
        """

        return self.handle_request(
            url=self._base_url + PaymentEndpoints.report_usage,
            json={
                'token': token,
                'id': str(uuid.uuid4()),
                'internalAppId': app_id,
                'internalProductId': product_id,
                'credits': credits,
                'metaData': meta,
            },
        )

    def verify_app_access(self, token: str, app_id: str) -> object:

        """Verify whether the user has access to a given app.

        :param token: User token.
        :param app_id: ID of the application.
        :returns: Object
        """

        return self.handle_request(
            url=self._base_url + PaymentEndpoints.verify,
            data={'token': token, 'internalAppId': app_id},
        )

    def report_app_usage(
        self,
        token: str,
        id: str,
        app_id: str,
        unit: str,
        units: int = 0,
        meta: dict = {},
    ) -> object:

        """Report usage for a given app.

        :param token: User token.
        :param id: Unique ID of the report, needs to be UUIDv4.
        :param app_id: ID of the application.
        :param unit: ID of the unit to report.
        :param units: Number of units to report.
        :param meta: Dictionary of metadata info attached to the report.
        :returns: Object
        """

        return self.handle_request(
            url=self._base_url + PaymentEndpoints.report_usage,
            json={
                'token': token,
                'id': id,
                'internalAppId': app_id,
                'unit': unit,
                'units': units,
                'metaData': meta,
            },
        )
