from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="coder-kali",
    version="1.0.0",
    author="Sammir Contreras",
    author_email="sammir@coderkali.local",
    description="Agente de IA de élite nativo para Kali Linux y distribuciones Linux (Pentesting, Ciberseguridad, DevOps).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sammir1209/coder-kali.git",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
        "Topic :: Security",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.9",
    install_requires=[
        "litellm>=1.40.0",
        "rich>=13.7.0",
        "typer>=0.12.0",
        "questionary>=2.0.1",
        "cryptography>=42.0.0",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        ":sys_platform != 'win32'": ["pexpect>=4.9.0"],
    },
    entry_points={
        "console_scripts": [
            "coder-kali=coder_kali.cli:main",
        ],
    },
    include_package_data=True,
)
