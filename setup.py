from setuptools import setup, find_packages

with open('Readme.md', encoding='utf-8') as f:
    readme = f.read()


setup(
    name='verify-squash-root',
    version='0.0.3',
    description='Build a signed efi binary which mounts a '
                'verified squashfs image as root',
    long_description=readme,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: Linux :: Arch Linux',
        'Environment :: Console'
    ],
    author='Simon Brand',
    author_email='simon.brand@postadigitale.de',
    url='https://github.com/brandsimon/verify-squash-root',
    keywords='Secure boot, squashfs, dm-verity',
    package_dir={'': 'src'},
    packages=find_packages('src/'),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'dev': ['pycodestyle', 'pyflakes'],
    },
    install_requires=[],
    entry_points={
        'console_scripts': [
            'verify-squash-root=verify_squash_root:parse_params_and_run'
        ]
    },
)
