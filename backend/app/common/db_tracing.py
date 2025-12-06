from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor


def setup_sqlalchemy_tracing(engine):
    SQLAlchemyInstrumentor().instrument(
        engine=engine.sync_engine,
        enable_commenter=True,
        commenter_options={}
    )
