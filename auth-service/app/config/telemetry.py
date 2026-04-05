from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


def setup_telemetry():
    resource = Resource.create({
        "service.name": "auth-service"
    })

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    exporter = OTLPSpanExporter(
        endpoint="http://jaeger:4317",
        insecure=True,
    )

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    # Auto-instrument
    DjangoInstrumentor().instrument()
    RequestsInstrumentor().instrument()