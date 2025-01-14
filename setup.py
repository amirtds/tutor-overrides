from setuptools import setup, find_packages

setup(
    name='tutor_overrides',
    version='0.0.1',
    author='Amir Tadrisi',
    author_email='amirtds@gmail.com',
    license='MIT',
    description='Customizing Tutor edx-platform',
    packages=find_packages(
        include=['tutor_overrides', 'tutor_overrides.*']
    ),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'lms.djangoapp': [
            'tutor_overrides = tutor_overrides.apps:TutorOverridesConfig',
        ],
},
)