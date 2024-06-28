from setuptools import setup, find_packages

with open('Readme.md', encoding='utf-8') as f:
    readme = f.read()


setup(
    name='verity-squash-root',
    version='0.3.5',
    description='Build a signed efi binary which mounts a '
                'verified squashfs image as rootfs',
    long_description=readme,
    long_description_content_type='text/markdown',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Linux :: Arch Linux',
        'Operating System :: Linux :: Debian',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Security :: Cryptography',
        'System :: Filesystems',
        'System :: Boot :: Init'
    ],
    author='Simon Brand',
    author_email='simon.brand@postadigitale.de',
    url='https://github.com/brandsimon/verity-squash-root',
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
            'verity-squash-root=verity_squash_root:parse_params_and_run'
        ]
    },
)
