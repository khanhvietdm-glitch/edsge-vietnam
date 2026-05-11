from setuptools import setup, find_packages

setup(
    name="edsge_vn",
    version="1.0.0",
    description="Climate-Integrated E-DSGE Replication Package for Vietnam",
    author="Vu Tuan Anh, Le Thi Thuy Giang, Pham Van Khanh",
    author_email="khanhvietdm@gmail.com",
    license="MIT",
    packages=find_packages(exclude=["tests", "scripts"]),
    install_requires=[
        "numpy>=1.24",
        "scipy>=1.10",
        "pandas>=2.0",
        "matplotlib>=3.7",
        "openpyxl>=3.1",
        "statsmodels>=0.14",
    ],
    python_requires=">=3.10",
)
