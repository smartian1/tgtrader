from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tgtrader",  
    version="0.1.0",
    author="smartian",
    author_email="smartian@163.com",
    description="TianGong Quantitative Investment Research Analysis Client",
    url="https://github.com/smartian1/tgtrader",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        'pandas==1.5.3',
        'numpy==1.26.4',
        'matplotlib==3.5.3',
        'ffn==1.1.1',
        'loguru',
        'akshare',
        'tqdm',
        'cython',
        'pyprind'
    ],
    package_data={
        'tgtrader': ['images/*'],
    },
    include_package_data=True,
    license='MPL-2.0',
)
