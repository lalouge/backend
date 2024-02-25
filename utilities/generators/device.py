import jwt, time
import datetime
import hashlib

class DeviceAuthenticator:
    def __init__(self, secret_key, token_expiry_minutes=15, refresh_token_expiry_days=30):
        self.secret_key = secret_key
        self.token_expiry_minutes = token_expiry_minutes
        self.refresh_token_expiry_days = refresh_token_expiry_days

    def generate_tokens(self, device_id):
        # Combine device ID and current timestamp for added uniqueness
        unique_identifier = f"{device_id}-{datetime.datetime.utcnow().timestamp()}"
        
        # Hash the unique identifier to generate a token
        token = hashlib.sha256(unique_identifier.encode()).hexdigest()

        print("TOKEN IS::: ", token)

        # Define the payload for both access and refresh tokens
        access_payload = {
            'device_id': device_id,
            "token": token,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=self.token_expiry_minutes)
        }

        refresh_payload = {
            'device_id': device_id,
            "token": token,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=self.refresh_token_expiry_days)
        }

        # Generate both access and refresh tokens
        access_token = jwt.encode(access_payload, self.secret_key, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm='HS256')

        return access_token, refresh_token

    def verify_access_token(self, token):
        try:
            # Decode and verify the access token
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            print("Access token has expired")
            return None
        except jwt.InvalidTokenError:
            print("Invalid access token")
            return None

    def revoke_refresh_token(self, refresh_token):
        # In a real system, you might want to maintain a list/database of revoked tokens
        # Here, we'll just print a message indicating token revocation
        print(f"Revoking refresh token: {refresh_token}")

    def get_access_token_from_refresh_token(self, refresh_token):
        try:
            # Decode and verify the refresh token
            refresh_payload = jwt.decode(refresh_token, self.secret_key, algorithms=['HS256'])
            
            # Check if the refresh token is still valid
            if datetime.datetime.utcnow() < datetime.datetime.utcfromtimestamp(refresh_payload['exp']):
                # Revoke the used refresh token
                self.revoke_refresh_token(refresh_token)
                
                # Generate a new access token
                new_access_token_payload = {
                    'device_id': refresh_payload['device_id'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=self.token_expiry_minutes)
                }
                new_access_token = jwt.encode(new_access_token_payload, self.secret_key, algorithm='HS256')
                
                # Generate a new refresh token
                new_refresh_token_payload = {
                    'device_id': refresh_payload['device_id'],
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=self.refresh_token_expiry_days)
                }
                new_refresh_token = jwt.encode(new_refresh_token_payload, self.secret_key, algorithm='HS256')

                return new_access_token, new_refresh_token
            else:
                print("Refresh token has expired")
                return None, None
        except jwt.InvalidTokenError:
            print("Invalid refresh token")
            return None, None


# Example usage
secret_key = 'your_secret_key'
authenticator = DeviceAuthenticator(secret_key)

# Simulate generating tokens for 3 billion devices
device_id = 1

access_token, refresh_token = authenticator.generate_tokens(str(device_id))

print("Access token:  " + access_token + " and Refresh Token  " + refresh_token)

print("Verify: ", authenticator.verify_access_token(access_token))

time.sleep(20)

print("\n regenerate: ", authenticator.get_access_token_from_refresh_token(refresh_token))
