import pytest

def app():
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',  # Use an in-memory database for tests
        'WTF_CSRF_ENABLED': False  # Disable CSRF tokens for testing forms
    })
    with flask_app.app_context():
        db.create_all()

    yield flask_app  # This provides the app context for tests

    with flask_app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

