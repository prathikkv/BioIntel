from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="biointel-ai",
    version="1.0.0",
    author="BioIntel.AI Team",
    author_email="support@biointel.ai",
    description="AI-powered bioinformatics platform for gene expression analysis and literature summarization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/biointel-ai/biointel",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
            "pre-commit>=3.6.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "biointel=api.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/**/*", "static/**/*"],
    },
    keywords="bioinformatics, ai, gene-expression, literature-mining, data-analysis",
    project_urls={
        "Bug Reports": "https://github.com/biointel-ai/biointel/issues",
        "Source": "https://github.com/biointel-ai/biointel",
        "Documentation": "https://docs.biointel.ai",
    },
)