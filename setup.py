from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='slc.onlinecontacts',
      version=version,
      description="This product provides a portlet labeled 'Who's online?' which shows you a list of all online users and enables you to contact them.",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='plone syslab.com portlet onlinecontacts',
      author='Syslab.com, JC Brand',
      author_email='brand@syslab.com',
      url='http://plone.org',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['slc'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'simplejson',
          'chat.server',
      ],
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
