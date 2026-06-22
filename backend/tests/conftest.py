import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Company
from app.config import settings

# Use in-memory SQLite for testing
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture
def session(db):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_company(session):
    company = Company(
        legal_name="Test Company GmbH",
        trade_name="Test Co.",
        hgb_reference_number="HB12345",
        currency="EUR",
        fiscal_year_end=12
    )
    session.add(company)
    session.commit()
    return company


@pytest.fixture
def sample_pdf_path():
    return "tests/fixtures/sample_jahresabschluss_2024.pdf"
