#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
------------------------------------------------------------------------------------------------------------------------
setup.py
Copyright (C) 2019-20 - NFStream Developers
This file is part of NFStream, a Flexible Network Data Analysis Framework (https://www.nfstream.org/).
NFStream is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
version.
NFStream is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with NFStream.
If not, see <http://www.gnu.org/licenses/>.
------------------------------------------------------------------------------------------------------------------------
"""

import sys
import os
import subprocess
import shutil

if (not sys.version_info[0] == 3) and (not sys.version_info[1] >= 6):
    sys.exit("Sorry, nfstream requires Python3.6+ versions.")


from setuptools import setup
from setuptools.command.build_ext import build_ext
from setuptools.command.build_py import build_py


this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


def setup_observer_cc():
    platform_compiler = "gcc"
    if sys.platform == 'darwin':
        platform_compiler = "clang"
    print("\nSetting up observer_cc. Platform: {plat}, Byteorder: {bo}".format(plat=sys.platform, bo=sys.byteorder))
    # compile libpcap and ship it with observer
    # we compile libpcap instead of copying the .so from to ensure 1.9.1 version on both mac OS and Linux
    subprocess.check_call(['git', 'clone', '--branch', 'libpcap-1.9.1',
                           'https://github.com/the-tcpdump-group/libpcap.git'])
    os.chdir('libpcap/')
    subprocess.check_call(['./configure', 'CC={}'.format(platform_compiler), '--enable-ipv6', '--disable-universal',
                           '--enable-dbus=no', '--without-libnl'])
    subprocess.check_call(['make'])
    os.chdir('..')
    subprocess.check_call([platform_compiler, '-shared', '-o', 'nfstream/observer_cc.so', '-g', '-fPIC', '-DPIC', '-O2', '-Wall',
                           'nfstream/observer_cc.c', 'libpcap/libpcap.a'])
    shutil.rmtree('libpcap/', ignore_errors=True)


def setup_meter_cc():
    platform_compiler = "gcc"
    if sys.platform == 'darwin':
        platform_compiler = "clang"
    print("\nSetting up meter_cc. Platform: {plat}, Byteorder: {bo}".format(plat=sys.platform, bo=sys.byteorder))
    subprocess.check_call(['git', 'clone', '--branch', 'dev', 'https://github.com/ntop/nDPI.git'])
    os.chdir('nDPI/')
    subprocess.check_call(['./autogen.sh'])
    subprocess.check_call(['./configure', 'CC={}'.format(platform_compiler),])
    os.chdir('src/')
    os.chdir('lib/')
    subprocess.check_call(['make'])
    # subprocess.check_call([platform_compiler, '-I../include', '-shared', '-o', '../../../nfstream/meter_cc.so',
    #                       '-g', '-fPIC', '-DPIC', '-O2', '-Wall', '../../../nfstream/meter_cc.c', 'libndpi.a'])
    shutil.copy2('libndpi.so', '../../../nfstream/')
    print("Setting up tests.")
    os.chdir('..')
    os.chdir('..')
    os.chdir('example/')
    subprocess.check_call(['make'])
    os.chdir('..')
    os.chdir('..')
    os.chdir('tests/')
    subprocess.check_call(['chmod', 'a+x', 'build_results.sh'])
    subprocess.check_call(['./build_results.sh'])
    os.chdir('..')
    shutil.rmtree('nDPI/', ignore_errors=True)


class BuildPyCommand(build_py):
    def run(self):
        self.run_command('build_native')
        build_py.run(self)


class BuildNativeCommand(build_ext):
    def run(self):
        if os.name != 'posix':  # Windows case
            pass
        else:
            setup_observer_cc()
            setup_meter_cc()
        build_ext.run(self)


needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []
python_requires = '>=3.6'
install_requires = ['cffi>=1.14.0',
                    'numpy<=1.18.5',
                    'pandas>=1.0.3',
                    'psutil>=5.7.0']

try:
    from wheel.bdist_wheel import bdist_wheel as _bdist_wheel

    class bdist_wheel(_bdist_wheel):
        def get_tag(self):
            tag = _bdist_wheel.get_tag(self)
            pypi_compliant_tag = list(tag)
            if 'linux' == pypi_compliant_tag[2][0:5]:
                pypi_compliant_tag[2] = pypi_compliant_tag[2].replace("linux", "manylinux1")
            if pypi_compliant_tag[2] == "manylinux1_aarch64":
                pypi_compliant_tag[2] = "manylinux2014_aarch64"
            pypi_compliant_tag = tuple(pypi_compliant_tag)
            return pypi_compliant_tag

        def finalize_options(self):
            _bdist_wheel.finalize_options(self)
            self.root_is_pure = False


except ImportError:
    print('Warning: cannot import "wheel" package to build platform-specific wheel')
    print('Install the "wheel" package to fix this warning')
    bdist_wheel = None

cmdclass = {'build_native': BuildNativeCommand,
            'build_py': BuildPyCommand,
            'bdist_wheel': bdist_wheel} if bdist_wheel is not None else dict()

setup(
    name="nfstream",
    version='5.3.0',
    url='https://www.nfstream.org/',
    license='LGPLv3',
    description="A Flexible Network Data Analysis Framework",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Zied Aouini',
    author_email='aouinizied@gmail.com',
    packages=['nfstream'],
    install_requires=install_requires,
    cmdclass=cmdclass,
    setup_requires=pytest_runner,
    tests_require=['pytest>=5.0.1'],
    include_package_data=True,
    platforms=["Linux", "Mac OS-X", "Unix"],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering :: Artificial Intelligence'
    ],
    project_urls={
        'GitHub': 'https://github.com/aouinizied/nfstream',
    }
)
