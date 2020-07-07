import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
    
setuptools.setup(
    name="python-fsapi-jri", # Replace with your own username
    version="0.0.10",
    author="James Inge",
    author_email="github@inge.org.uk",
    description="A Python implementation of the Frontier Silicon API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JRInge/python-fsapi",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)