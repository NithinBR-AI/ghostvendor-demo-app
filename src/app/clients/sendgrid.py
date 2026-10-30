'''SendGrid API client — intentionally has no retry, timeout, or error handling.'''

import os
import random
import time
import uuid

import requests


def send_email(to: str, subject: str, body: str, from_email: str = 'noreply@ghostvendor.dev') -> int:
    idempotency_key = str(uuid.uuid4())
    for attempt in range(3):
        try:
            base_url = os.environ.get('SENDGRID_BASE_URL', 'https://api.sendgrid.com')
            api_key = os.environ['SENDGRID_API_KEY']
            response = requests.post(
                f'{base_url}/v3/mail/send',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'Idempotency-Key': idempotency_key,
                },
                json={
                    'personalizations': [{'to': [{'email': to}]}],
                    'from': {'email': from_email},
                    'subject': subject,
                    'content': [{'type': 'text/plain', 'value': body}],
                },
                timeout=10,
            )
        except requests.exceptions.Timeout:
            return {'error': 'timeout', 'message': 'SendGrid request timed out'}
        except requests.exceptions.ConnectionError:
            return {'error': 'connection_error', 'message': 'Could not connect to SendGrid'}
        except requests.exceptions.RequestException:
            return {'error': 'request_error', 'message': 'SendGrid request failed'}
        if response.status_code >= 400 and response.status_code not in (429, 502, 503):
            return {'error': 'vendor_error', 'status_code': response.status_code}
        if response.status_code in (429, 502, 503):
            if attempt < 2:
                retry_after = response.headers.get('Retry-After')
                if response.status_code == 429 and retry_after is not None:
                    try:
                        sleep_seconds = min(int(retry_after), 10)
                    except ValueError:
                        sleep_seconds = 2 ** attempt
                else:
                    sleep_seconds = 2 ** attempt
                time.sleep(sleep_seconds + random.uniform(0, 0.5))
                continue
            return {'error': 'vendor_error', 'status_code': response.status_code}
        if response.text:
            try:
                parsed = response.json()
            except ValueError:
                return {'error': 'malformed_response', 'message': 'SendGrid returned non-JSON response'}
            if not isinstance(parsed, dict) or not parsed:
                return {'error': 'empty_response', 'message': 'SendGrid returned empty response body'}
            return parsed
        return {'status_code': response.status_code}
    return {'error': 'vendor_error', 'status_code': response.status_code}
