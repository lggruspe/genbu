import setuptools

with open("README.md") as file:
    long_description = file.read()

setuptools.setup(
    name="infer_parser",
    version="0.1.0",
    author="Levi Gruspe",
    author_email="mail.levig@gmail.com",
    description="Make shell argument parsers from type hints",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lggruspe/infer-parser",
    packages=setuptools.find_packages(),
    package_data={
        "infer_parser": ["py.typed"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires=">=3.6",
)
