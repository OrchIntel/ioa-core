#!/usr/bin/env python3
"""
IOA Core - Intelligent Orchestration Architecture
Setup configuration for pip installation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="ioa-core",
    version="2.4.8",
    author="IOA Project Contributors",
    author_email="maintainers@ioaproject.org",
    description="Multi-agent orchestration framework with memory-driven collaboration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ioa-project/ioa-core",
    project_urls={
        "Bug Reports": "https://github.com/ioa-project/ioa-core/issues",
        "Source": "https://github.com/ioa-project/ioa-core",
        "Documentation": "https://github.com/ioa-project/ioa-core/blob/main/README.md",
        "Security": "https://github.com/ioa-project/ioa-core/blob/main/SECURITY.md",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.9",
    install_requires=requirements if requirements else [
        "openai>=1.0.0",
        "pydantic>=2.0.0",
        "PyYAML>=6.0",
        "python-dotenv>=1.0.0",
        "click>=8.0.0",
        "jsonschema>=4.0.0",
        "pathlib-mate>=1.0.0",
        "typing-extensions>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "enterprise": [
            # Placeholder - Enterprise features require separate licensing
            # Contact enterprise@orchintel.com for IOA Enterprise
        ],
        "optional": [
            "spacy>=3.4.0",  # For advanced NLP (future enhancement)
            "pandas>=1.5.0",  # For data analysis features
            "numpy>=1.21.0",  # For numerical computations
        ],
    },
    entry_points={
        "console_scripts": [
            "ioa=src.cli_interface:main",
            "ioa-boot=src.bootloader:main",
            "ioa-onboard=src.agent_onboarding:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": [
            "config/*.yaml",
            "config/*.json",
            "patterns.json",
            "*.md",
        ],
    },
    zip_safe=False,
    keywords=[
        "ai", "agents", "orchestration", "memory", "collaboration",
        "multi-agent", "governance", "pattern-matching", "nlp"
    ],
    license="Apache 2.0",
    platforms=["any"],
    
    # Security and compliance metadata
    options={
        "bdist_wheel": {
            "universal": False,  # Python 3 only
        },
    },
    
    # Development status and maintenance
    maintainer="IOA Project Team",
    maintainer_email="maintainers@ioaproject.org",
    
    # Additional metadata for PyPI
    provides=["ioa_core"],
    obsoletes=[],
    
    # Test configuration
    test_suite="tests",
    tests_require=[
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
    ],
)
