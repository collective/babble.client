from setuptools import setup, find_packages
import os

version = '1.3.2'

tests_require=[]

setup(
    name='babble.client',
    version=version,
    description="Babble: Instant messaging client for Plone",
    long_description=open("README.txt").read() + "\n" +
                    open(os.path.join("docs", "HISTORY.txt")).read() +
                    open(os.path.join("docs", "CONTRIBUTORS.txt")).read(),
    # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
    "Framework :: Plone",
    "Programming Language :: Python",
    ],
    keywords='plone syslab.com portlet onlinecontacts',
    author='Syslab.com, JC Brand',
    author_email='brand@syslab.com',
    url='http://plone.org/products/babble.client',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    namespace_packages=['babble'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'simplejson',
        'babble.server',
        'collective.js.blackbird',
    ],
    tests_require=tests_require,
    extras_require=dict(tests=tests_require),
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    """,
    )
