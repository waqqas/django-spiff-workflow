from setuptools import find_packages, setup

setup(
    name="django_spiff_workflow",
    version="0.1",
    packages=find_packages(),
    description="Django integration with spiff-workflow",
    author="Waqqas Jabbar",
    author_email="waqqas.jabbar@egmail.com",
    url="https://github.com/waqqas/django_spiff_workflow/",
    license="MIT",
    install_requires=[
        "Django",
        "spiffworkflow",
        "restrictedpython",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
    ],
    include_package_data=True,
    zip_safe=False,
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="django spiff-workflow",
)
