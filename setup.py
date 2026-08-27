from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="blood-cipher",
    version="2.0.0",
    author="CODER",
    author_email="blood-chipher@root.com",
    description="Blood-Cipher - Agente de IA de élite para ciberseguridad, hacking ético y auditorías en Linux (Kali, BlackArch, Arch, Debian).",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Sammir1209/blood-cipher.git",
    keywords=[
        "blood-cipher",
        "hacktivism",
        "osint",
        "digital-sovereignty",
        "kali-linux",
        "blackarch",
        "penetration-testing",
        "ethical-hacking",
        "security-audit",
        "ai-agent",
        "vulnerability-scanner",
        "network-audit",
        "hash-cracker",
        "red-team",
    ],
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
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
        "orjson>=3.9.0",
    ],
    extras_require={
        ":sys_platform != 'win32'": [
            "pexpect>=4.9.0",
            "uvloop>=0.19.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "blood-cipher=coder_kali.cli:main",
        ],
    },
    include_package_data=True,
)
