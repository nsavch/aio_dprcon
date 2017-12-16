from setuptools import setup, find_packages


setup(name='aio-dprcon',
      version='0.1.5',
      description='library and console client for DarkPlaces RCON protocol',
      long_description=open('README.rst').read(),
      url='https://github.com/nsavch/aio_dprcon',
      author='Nick Savchenko',
      author_email='nsavch@gmail.com',
      license='GPLv3',
      packages=find_packages(),
      keywords='xonotic',
      install_requires=[
          'setuptools',
          'click',
          'colorama',
          'python-dpcolors',
          'PyYAML'
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: System Administrators',
          'Intended Audience :: Developers',
          'Intended Audience :: Other Audience',  # gamers
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3 :: Only',
          'Programming Language :: Python :: Implementation :: CPython',
          'Topic :: Software Development :: Libraries',
          'Topic :: Games/Entertainment',
      ],
      entry_points={
          'console_scripts': [
              'dprcon=aio_dprcon.cli:cli'
          ]
      })
