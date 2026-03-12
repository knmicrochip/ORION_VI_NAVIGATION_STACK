from setuptools import find_packages, setup

import os
from glob import glob

package_name = 'button_detection_pkg'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*_launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=[
        'setuptools',
        'ultralytics',
        'opencv-python',
        'numpy',
    ],
    zip_safe=True,
    maintainer='geoglof',
    maintainer_email='jakubgoleman12@gmail.com',
    description='YOLO-based button/switch detection for ERC 2026 Maintenance Task panel.',
    license='Apache-2.0',
    extras_require={
        'test': ['pytest'],
        'train': ['ultralytics', 'roboflow'],
    },
    entry_points={
        'console_scripts': [
            'detector_node = button_detection_pkg.detector_node:main',
            'aruco_fusion_node = button_detection_pkg.aruco_fusion:main',
        ],
    },
)
