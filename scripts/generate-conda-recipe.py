import yaml

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
    with open(file, 'r') as fr:
        read_lines = fr.readlines()

    with open(file, 'w') as fw:
        write_lines = ''.join(read_lines[line:])
        fw.write(write_lines)


def get_lines(file: str, start: int, end: int):
    with open(file, 'r') as fr:
        read_lines = fr.readlines()
    return read_lines[ start:end ]


def generate_meta_yaml(source_path: str, target_path: str):

    save_lines = get_lines(source_path, 0, 2)
    delete_lines(source_path, 2)

    with open(source_path) as f:
        meta_dict = yaml.safe_load(f)
    
        meta_dict['package'] = {'name': '<{ name|lower }>', 'version': '<{ version }>'}
        meta_dict['build']['noarch'] = 'python'
        if(meta_dict['requirements'] and meta_dict['requirements']['host']):
            meta_dict['requirements']['host'] = ['docker-py' if item == 'docker' else item for item in meta_dict['requirements']['run']]
        if(meta_dict['requirements'] and meta_dict['requirements']['run']):
            meta_dict['requirements']['run'] = ['docker-py' if item == 'docker' else item for item in meta_dict['requirements']['run']]

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

    with open(source_path, 'w+') as fp:
        fp.write(recipe)

    with open(target_path, 'w+') as fp:
        fp.write(recipe)

generate_meta_yaml("conda/floralatin-hubble-sdk/meta.yaml", 'conda/meta.yaml')