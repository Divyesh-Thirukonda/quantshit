from setuptools import setup, find_packages

setup(
    name="quantshit",
    version="0.1.0",
    description="Trading bot for prediction markets with backtesting engine",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "python-dateutil>=2.8.0",
    ],
    python_requires=">=3.8",
)
