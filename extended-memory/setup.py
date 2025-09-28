from setuptools import setup, find_packages

setup(
    name="esm",
    version="1.0.0",
    description="Extended Sienna Memory - AI Memory System",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "sqlalchemy>=2.0.23",
        "alembic>=1.12.1",
        "psycopg2-binary>=2.9.9",
        "pydantic>=2.5.0",
        "httpx>=0.25.2",
        "openai>=1.3.7",
        "typesense>=0.15.0",
        "click>=8.1.7",
    ],
    entry_points={
        "console_scripts": [
            "esm=esm.cli:main",
        ],
    },
)