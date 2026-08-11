from setuptools import find_packages, setup

import os
from glob import glob

package_name = 'orion_vi_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.xacro')),
        (os.path.join('share', package_name, 'urdf/sensors'), glob('urdf/sensors/*.xacro')),
        (os.path.join('share', package_name, 'urdf/sensors/Intel_RealSense_D435/materials/scripts'), glob('urdf/sensors/Intel_RealSense_D435/materials/scripts/*.materials')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.sdf')),
        (os.path.join('share', package_name, 'urdf/sensors/Intel_RealSense_D435/materials/textures'), glob('urdf/sensors/Intel_RealSense_D435/materials/textures/*.png')),
        (os.path.join('share', package_name, 'urdf/meshes'), glob('urdf/meshes/*.glb')),
        (os.path.join('share', package_name, 'urdf/meshes'), glob('urdf/meshes/*.dae')),
        (os.path.join('share', package_name, 'urdf/meshes'), glob('urdf/meshes/*.obj')),
        (os.path.join('share', package_name, 'urdf/meshes'), glob('urdf/meshes/*.mtl')),
        (os.path.join('share', package_name, 'urdf/meshes'), glob('urdf/meshes/*.stl')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Bungok',
    maintainer_email='ignacy@piekarczyk.pl',
    description='TODO: Package description',
    license='Apache 2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
