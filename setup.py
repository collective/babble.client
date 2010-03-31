from setuptools import setup, find_packages
import os

version = '1.0'

tests_require=[]

setup(
    name='babble.client',
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
