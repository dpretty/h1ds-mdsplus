from distutils.core import setup

execfile('h1ds_mdsplus/version.py')

setup(name='h1ds_mdsplus',
      version=__version__,
      packages=['h1ds_mdsplus'],
      package_data={'h1ds_core':['templates/*/*.html']}
      )
