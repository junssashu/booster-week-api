from rest_framework.renderers import JSONRenderer


class CustomJSONRenderer(JSONRenderer):
    """Wrap single-object responses in {data: ...} envelope.

    Skip wrapping if:
    - Response already contains 'data' or 'error' key
    - Response is a paginated response (has 'pagination' key)
    - Response is a list (paginator handles wrapping)
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return super().render(data, accepted_media_type, renderer_context)

        response = renderer_context.get('response') if renderer_context else None

        # Don't wrap error responses
        if response and response.status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)

        # Don't wrap if already wrapped or paginated
        if isinstance(data, dict) and ('data' in data or 'error' in data or 'pagination' in data or 'received' in data):
            return super().render(data, accepted_media_type, renderer_context)

        # Wrap in data envelope
        wrapped = {'data': data}
        return super().render(wrapped, accepted_media_type, renderer_context)
