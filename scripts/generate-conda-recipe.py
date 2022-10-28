import os
import shutil

root_path = './conda'
package_name = 'jina-hubble-sdk'

def generate_meta_yaml_from_pypi(package_name):
    maintainers = 'mapleeit,nomagick,delgermurun,Andrei997,floralatin'
    command = f'grayskull pypi --strict-conda-forge {package_name} '
    command = command + f' -m {maintainers} '
    command = command + f' --output {root_path} '
    os.system(command)

def generate_meta_yaml():
    """Generate conda meta yaml"""

    generate_meta_yaml_from_pypi(package_name)
    shutil.copy(f'{root_path}/{package_name}/meta.yaml', f'{root_path}/meta.yml')
    shutil.rmtree(f'{root_path}/{package_name}')

generate_meta_yaml()