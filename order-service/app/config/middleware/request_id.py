import uuid
from config.logging.filters import set_request_id


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # store globally for logging
        set_request_id(request_id)

        # attach to request
        request.request_id = request_id

        response = self.get_response(request)

        # return request id to client
        response["X-Request-ID"] = request_id

        return response