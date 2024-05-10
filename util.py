import os
from xml.etree import ElementTree
from streamlit.runtime.uploaded_file_manager import UploadedFile


CHILDREN = 'children'
LABEL = 'label'
VALUE = 'value'


def get_tag_name(tag:         str,
                 parent_path: str,
                 ignore_ns:   bool) -> {str, str}:
    split = tag.split("}")
    name = split[1] if ignore_ns and len(split) > 1 else tag
    subpath = (parent_path + '/' if len(parent_path) > 0 else '') + name
    return name, subpath


def get_node_name(node:        ElementTree,
                  parent_path: str,
                  ignore_ns:   bool) -> {str, str}:
    return get_tag_name(node.tag, parent_path, ignore_ns)


def prefix_field_name(field:     str,
                      prefix:    str) -> str:
    return prefix + field


def save_temp_file(file: UploadedFile) -> str:
    folder = 'tmp'
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    file_path = f'./{folder}/{file.name}'
    with open(file_path, 'wb') as f:
        f.write(file.getvalue())

    return file_path
