# setup.py

from setuptools import setup, find_packages

setup(
    name="photo_organizer",
    version="1.6.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "photo-organizer=photo_organizer.main:main",
        ],
    },
    install_requires=["tqdm"],
    author="Supporterino",
    author_email="lars@roth-kl.de",
    description="A script to organize photos by creation date into year/month/day folders.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Supporterino/photo-organizer",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
