from pathlib import Path
import setuptools

setuptools.setup(
    name="genbu",
    version="0.1",
    author="Levi Gruspe",
    author_email="mail.levig@gmail.com",
    description="Create CLIs using parser combinators and type hints",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    url="https://github.com/lggruspe/genbu-parser",
    packages=setuptools.find_packages(),
    package_data={
        "genbu": ["py.typed"],
    },
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
)
