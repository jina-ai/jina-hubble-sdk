import yaml
import sys

class RecipeDumper(yaml.SafeDumper):
    """Adds a line break between top level objects and ignore aliases"""

    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()

    def ignore_aliases(self, data):
        return True

    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)


def delete_lines(file: str, line: int):
    """Delete a line from the file head"""
    with open(file, 'r') as fr:
        read_lines = fr.readlines()

    with open(file, 'w') as fw:
        write_lines = ''.join(read_lines[line:])
        fw.write(write_lines)


def get_lines(file: str, start: int, end: int):
    """Get lines from the file"""

    with open(file, 'r') as fr:
        read_lines = fr.readlines()
    return read_lines[ start:end ]


def replace_package_name(requirements: list, old: str, new: str):
    """replace package name"""

    replace_requirements = []
    for package_name in requirements:
        if package_name == old:
            replace_requirements.append(new)
        else:
            replace_requirements.append(package_name)
    return replace_requirements 


def generate_meta_yaml(meta_path: str):
    """Generate conda meta yaml"""

    save_lines = get_lines(meta_path, 0, 2)
    delete_lines(meta_path, 2)

    with open(meta_path) as f:
        meta_dict = yaml.safe_load(f)
        meta_dict['package'] = {'name': '<{ name|lower }>', 'version': '<{ version }>'}

        # build noarch package
        meta_dict['build']['noarch'] = 'python'
        
        if(meta_dict['requirements'] and meta_dict['requirements']['host']):
            meta_dict['requirements']['host'] = replace_package_name(meta_dict['requirements']['host'], 'docker', 'docker-py')

        if(meta_dict['requirements'] and meta_dict['requirements']['run']):
            meta_dict['requirements']['run'] = replace_package_name(meta_dict['requirements']['run'], 'docker', 'docker-py')

    recipe = yaml.dump(
        meta_dict,
        Dumper=RecipeDumper,
        width=1000,
        sort_keys=False,
        default_style=None,
    )
    recipe = recipe.replace('<{', '{{').replace('}>', '}}')

    recipe_header = ''
    for line in save_lines:
        recipe_header =  f'{recipe_header}{line}'
    recipe = recipe_header + recipe

    with open(meta_path, 'w+') as fp:
        fp.write(recipe)


generate_meta_yaml(sys.argv[1])