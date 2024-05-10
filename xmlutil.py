from xml.etree import ElementTree

from util import (
  get_node_name, get_tag_name, prefix_field_name, CHILDREN, LABEL, VALUE
)

COUNT = 'count'
LIST = 'list'


class XML2TreeSelect:

    @staticmethod
    def add_child_node(target_node: dict,
                       name:        str,
                       subpath:     str) -> dict:
        if CHILDREN not in target_node:
            target_node[CHILDREN] = []

        for child in target_node[CHILDREN]:
            if child[LABEL] == name:
                child[COUNT] += 1
                return child

        child = {LABEL: name, VALUE: subpath, COUNT: 1, LIST:False}
        target_node[CHILDREN].append(child)
        return child


    @staticmethod
    def recursive_analyse_xml(root:        ElementTree,
                              parent_path: str,
                              target_node: dict,
                              ignore_ns:   bool):

        subpaths = []
        for attrib in root.keys():
            name, subpath = get_tag_name(attrib, parent_path, ignore_ns)
            child = XML2TreeSelect.add_child_node(target_node, name, subpath)
            if subpath in subpaths:
                child[LIST] = True
            else:
                subpaths.append(subpath)

        for node in root:
            name, subpath = get_node_name(node, parent_path, ignore_ns)
            child = XML2TreeSelect.add_child_node(target_node, name, subpath)
            if subpath in subpaths:
                child[LIST] = True
            else:
                subpaths.append(subpath)

            XML2TreeSelect.recursive_analyse_xml(node, subpath, child, ignore_ns)


    @staticmethod
    def recursive_add_count(node:    dict,
                            checked: list):
        count = node[COUNT]

        if node[LIST]:
            node[LABEL] += f': [{count}]'
            checked.append(node[VALUE])

        elif count > 1:
            node[LABEL] += f': ({count})'

        if CHILDREN in node:
            for child in node[CHILDREN]:
                XML2TreeSelect.recursive_add_count(child, checked)

    @staticmethod
    def convert(root:      ElementTree,
                ignore_ns: bool) -> {dict, list}:
        name, subpath = get_node_name(root, "", ignore_ns)
        struct = {LABEL: name, VALUE: subpath, COUNT : 1, LIST:False}
        XML2TreeSelect.recursive_analyse_xml(root, name, struct, ignore_ns)
        checked = []
        XML2TreeSelect.recursive_add_count(struct, checked)
        return struct, checked
