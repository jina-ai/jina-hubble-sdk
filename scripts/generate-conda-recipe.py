import os
import shutil
import sys

root_path = 'conda'
package_name = 'jina-hubble-sdk'
tag = None

def generate_meta_yaml_from_pypi(package_name: str, tag: str or None):
    """Generate conda meta yaml from pypi"""

    maintainers = 'mapleeit nomagick delgermurun Andrei997 floralatin'

    final_package_name = f'{package_name}=={tag}' if tag else package_name
    command = f'grayskull pypi --strict-conda-forge {final_package_name} '
    command = command + f' -m {maintainers} '
    command = command + f' --output {root_path} '
    
    os.system(command)

def generate_meta_yaml(package_name: str, tag: str):
    """Generate conda meta yaml"""

    generate_meta_yaml_from_pypi(package_name, tag)
    shutil.copy(f'{root_path}/{package_name}/meta.yaml', f'{root_path}/meta.yaml')
    shutil.rmtree(f'{root_path}/{package_name}')

if (len(sys.argv)>=2):
    package_name = sys.argv[1]

if (len(sys.argv)>=2):
    tag = sys.argv[2]

generate_meta_yaml(package_name, tag)