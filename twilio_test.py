import json
from twilio.rest import Client

with open('/Users/tnightengale/Desktop/Projects/twilio_sw_calling/authorizations.json') as file:
	key = json.load(file)

# Your Account Sid and Auth Token from twilio.com/console
account_sid = 'ACd56857607c7a0b13b56bc4736e07e5d0'
auth_token = '53224f3e0ed46f49da88e16c2bdbfdde'

client = Client(account_sid, auth_token)

call = client.calls.create(
                        url='https://handler.twilio.com/twiml/EH3b2f661c7cefb00d2c84350ab3971600',
                        to='+16134844779',
                        from_='+16473605398'
                    )

print(call.sid)