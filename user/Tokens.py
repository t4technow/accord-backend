from django.contrib.auth.tokens import PasswordResetTokenGenerator

class CustomTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + user.username + str(timestamp)

    def make_token(self, user):
        timestamp = int(time.time())
        return self._make_hash_value(user, timestamp)

    def check_token(self, user, token):
        if not (user and token):
            return False

        # Extract the ID and username from the provided token
        try:
            user_id, username, _ = token.split('-')
        except ValueError:
            return False

        # Compare the extracted ID and username with the user's ID and username
        return str(user.pk) == user_id and user.username == username
