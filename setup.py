import setuptools
with open("README.md","r") as fp:
    long_description = fp.read()


setuptools.setup(
    name="TEOPS",
    version="0.1a",
    author="septillioner",
    author_email="septillioner@protonmail.com",
    description="Easy socket for python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Septillioner/TEOPS",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 2.7.15",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires='>=2.7.10'
)