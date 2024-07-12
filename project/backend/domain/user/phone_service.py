from twilio.rest import Client

# Twilio credentials
account_sid = 'your_account_sid'
auth_token = 'your_auth_token'
verification_service_sid = 'your_verification_service_sid'

client = Client(account_sid, auth_token)


def send_verification_code(phone_number: str):
    verification = client.verify.services(verification_service_sid).verifications.create(to=phone_number, channel='sms')
    return verification.sid


def check_verification_code(phone_number: str, code: str):
    verification_check = client.verify.services(verification_service_sid).verification_checks.create(to=phone_number, code=code)
    return verification_check.status == 'approved'