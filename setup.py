from setuptools import setup, find_packages

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define package metadata
AUTHOR_NAME = 'Pranay Nambiar'
SRC_REPO = 'src'
LIST_OF_REQUIREMENTS = ['streamlit']

# Setup function
setup(
    name=SRC_REPO,
    version='0.0.1',
    author=AUTHOR_NAME,
    description='A Python-based movie recommender system',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),  # Automatically finds packages
    python_requires='>=3.7',  
    install_requires=LIST_OF_REQUIREMENTS,  
)
