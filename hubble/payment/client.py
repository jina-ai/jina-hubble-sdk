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
        :returns: JWT as string.
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
            decoded = self.validate_jwt(token)
            is_authorized = decoded.get('paymentAuthorized', False)
            return is_authorized
        except Exception:
            return False
