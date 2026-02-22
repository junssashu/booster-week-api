from rest_framework.throttling import SimpleRateThrottle


class CustomWindowThrottle(SimpleRateThrottle):
    """Base throttle supporting custom time windows like '10/15min'."""

    def parse_rate(self, rate):
        if rate is None:
            return (None, None)
        num, period = rate.split('/')
        num_requests = int(num)

        # Support formats: 15min, 30sec, 2hour, 1day, or standard m/h/d/s
        import re
        match = re.match(r'^(\d+)?(min|sec|hour|day|[smhd])$', period)
        if match:
            multiplier = int(match.group(1)) if match.group(1) else 1
            unit = match.group(2)
            unit_map = {
                's': 1, 'sec': 1,
                'm': 60, 'min': 60,
                'h': 3600, 'hour': 3600,
                'd': 86400, 'day': 86400,
            }
            duration = unit_map[unit] * multiplier
        else:
            # Fallback to DRF default: first char lookup
            duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]

        return (num_requests, duration)


class AuthRateThrottle(CustomWindowThrottle):
    scope = 'auth'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class ForgotPasswordThrottle(CustomWindowThrottle):
    scope = 'forgot_password'

    def get_cache_key(self, request, view):
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request),
        }


class PaymentThrottle(CustomWindowThrottle):
    scope = 'payment'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident,
        }


class QCMThrottle(CustomWindowThrottle):
    scope = 'qcm'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident,
        }


class TestimonyThrottle(CustomWindowThrottle):
    scope = 'testimony'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident,
        }
