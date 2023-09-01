from setuptools import setup, find_packages

setup(
    name='videoinr',
    version='1.0',
    packages=find_packages(),
    data_files=[('', ['README.md'])],
    install_requires=[
        'torch==2.0.1',
        'torchvision==0.15.2',
        'pyyaml',
        'tqdm',
        'Pillow',
        #'python-lmdb',
        'opencv-python',
        #'miss_hit',
    ],
    extras_require={
        'optional': [
            'ipython',
            'ipykernel',
        ],
    },
)
