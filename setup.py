from setuptools import setup, find_packages

setup(
    name="lambda_monitor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn>=0.24.0",
        "sqlalchemy>=2.0.0",
        "tweepy>=4.14.0",
        "httpx>=0.26.0",
        "python-dotenv>=1.0.0",
        "google-generativeai>=0.3.0",
        "transformers>=4.35.0",
        "torch>=2.0.0",
        "selenium>=4.15.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "pandas>=2.0.0"
    ],
    python_requires=">=3.9",
)
