
import logging
from django.conf import settings
from opentelemetry.trace import get_current_span

class ServiceNameFilter(logging.Filter):
    def filter(self, record):
        record.service = getattr(settings, "SERVICE_NAME", "unknown-service")
        return True


# Thread-local storage for request ID
import threading
_local = threading.local()


def set_request_id(request_id):
    _local.request_id = request_id


def get_request_id():
    return getattr(_local, "request_id", "unknown")


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = get_request_id()
        return True

class TraceIDFilter(logging.Filter):
    def filter(self, record):
        span = get_current_span()
        ctx = span.get_span_context()

        if ctx and ctx.trace_id != 0:
            record.trace_id = format(ctx.trace_id, "032x")
        else:
            record.trace_id = "unknown"
        return True