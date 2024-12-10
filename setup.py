from setuptools import setup, find_packages

setup(
    packages=find_packages(),
    include_package_data=True,  # 确保 package_data 生效
)
