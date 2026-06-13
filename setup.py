from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="solid-waste-chip-remanufacturing",
    version="1.0.0",
    author="Project Team",
    description="数据中心芯片二次利用系统 - 知识图谱、特征优化、强化学习、增量学习的完整框架",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "pandas>=2.0",
        "numpy>=1.24",
        "scikit-learn>=1.3",
        "tensorflow>=2.13",
        "torch>=2.0",
        "pyyaml>=6.0",
        "jupyter>=1.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0", "black>=23.0", "flake8>=6.0"],
        "ml": ["tensorflow>=2.13", "torch>=2.0", "stable-baselines3>=2.0"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
