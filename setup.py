from setuptools import setup, find_packages

setup(
    name="devagent",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "python-telegram-bot>=21.0",
        "anthropic>=0.39.0",
        "openai>=1.50.0",
        "aiosqlite>=0.20.0",
        "python-dotenv>=1.0.0",
        "tree-sitter>=0.23.0",
        "tree-sitter-python>=0.23.0",
        "tree-sitter-javascript>=0.23.0",
        "tree-sitter-typescript>=0.23.0",
        "gitpython>=3.1.40",
        "chromadb>=0.5.0",
        "httpx>=0.27.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0",
            "pytest-asyncio>=0.24.0",
            "pytest-cov>=5.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "devagent=agent.core:main",
        ],
    },
)
