"""Generates documentation for the Atrinik Python package.

The documentation is generated in the form of Python files that mimic the
C interface. Only the API is exposed, there is no implementation.

Documentation is collected from (and also dynamically generated ) docstrings
found in Atrinik classes, methods, etc.

The generated documentation is in Restructured Text (reST) format, and can be
found in /maps/python/Atrinik.

IDEs that support the reST format (such as PyCharm) can use this generated
Python interface to add type-hinting to functions and methods, and to even
resolve the Atrinik package definitions.
"""

import sys
import inspect
import os
import re
from collections import OrderedDict
import datetime
import textwrap

from Atrinik import *
from CParser import CParser


PATH = os.path.join(GetSettings()["mapspath"], "python", "Atrinik")


def getargspec(obj, obj_name):
    if not obj.__doc__:
        return []

    match = re.search(r"[\w_]+\((.*)\)", obj.__doc__, re.M)
    if not match:
        if obj_name.startswith("__") and obj_name.endswith("__"):
            return ["self"]

        print("Failed to get args for {}".format(obj))
        return []

    args = re.findall(r"([\w+_\*]+)(?:=([\w_\-\.]+))?", match.group(1))
    return ["=".join(x for x in val if x) for val in args]


def dump_docstring(obj, f, indent=0, obj_name=None, is_getter=False,
                   is_setter=False, doc=None):
    if doc is None:
        doc = obj.__doc__

    if not doc:
        return

    ret = None

    if is_getter or is_setter:
        parts = doc.split(";")
        if obj_name.startswith("f_"):
            parts.append("bool")
        if len(parts) < 2:
            print("Invalid object {}".format(obj))
            return
        types = re.match(r"([^\(]+)\s*(\(.*\))?", parts[1])
        if not types:
            print("No types for {}".format(obj))
            return

        tmp_type = types.group(1).strip()
        extra = types.group(2) or ""
        doc = parts[0].strip() + " " + extra.strip()

        ret = []
        types = []
        for val in tmp_type.split(" "):
            if val != "or":
                ret.append(val)
                types.append(":class:`{}`".format(val))

        if is_getter:
            doc += "\n\n:type: " + " or ".join(types)
        else:
            doc += "\n\n:param value: The value to set.\n"
            doc += ":type value: {}".format(" or ".join(ret))
    elif obj_name is not None:
        doc = ".. class:: {}\n\n".format(obj_name) + doc

    f.write(" " * indent * 4)
    f.write('"""\n')
    iterator = iter(doc.split("\n"))

    for line in iterator:
        if line.startswith(".. function::") or \
                line.startswith(".. method::") or line.startswith(".. class::"):
            next(iterator)
            continue

        subsequent_indent = " " * indent * 4
        if line.startswith(":"):
            subsequent_indent += " " * 2

        line = " " * indent * 4 + line
        line = textwrap.fill(line, width=80,
                             subsequent_indent=subsequent_indent)
        f.write(line + "\n")

    f.write(" " * indent * 4)
    f.write('"""\n')

    return ret


def open_doc_file(path):
    f = open(path, "w")
    f.write("# !!! This file was automatically generated by the Atrinik "
            "server. !!!\n# !!! Do NOT edit. !!!\n")
    f.write("# {name}\n".format(name=os.path.basename(path)))
    now = datetime.datetime.now()
    f.write("# Date of creation: {date}\n\n".format(date=now))
    return f


def dump_obj(obj, f, indent=0, defaults=None):
    names = []
    imports = []
    instances = []
    
    l = dir(obj)
    if defaults is not None:
        l += list(defaults.keys())

    for tmp_name in l:
        if tmp_name.startswith("__") and tmp_name.endswith("__"):
            if tmp_name not in ("__len__", "__bool__", "__iter__", "__next__",
                                "__getitem__"):
                continue

        if tmp_name == "print":
            continue

        if hasattr(obj, tmp_name):
            tmp = getattr(obj, tmp_name)
            doc = None
        else:
            tmp = defaults[tmp_name][0]
            doc = defaults[tmp_name][1]

        if inspect.ismodule(tmp):
            imports.append("import Atrinik.{name} as {name}\n".format(name=tmp_name))

            with open_doc_file(os.path.join(PATH, tmp_name + ".py")) as f2:
                dump_docstring(tmp, f2, indent)
                f2.write("# noinspection PyUnresolvedReferences\n")
                f2.write("import Atrinik\n")
                dump_obj(tmp, f2)
        elif tmp_name == "AtrinikError":
            f.write("\n\nclass {}(Exception):\n".format(tmp_name))
            dump_docstring(tmp, f, indent + 1, obj_name=tmp_name)
            dump_obj(tmp, f, indent=1)
        elif inspect.isclass(tmp):
            f.write("\n\n")
            f.write(" " * indent * 4)
            f.write("class {}(object):\n".format(tmp_name))
            dump_docstring(tmp, f, indent + 1, obj_name=tmp_name)
            dump_obj(tmp, f, indent=1)
        elif hasattr(tmp, "__call__"):
            args = getargspec(tmp, tmp_name)
            if inspect.isclass(obj):
                if not tmp_name.startswith("__"):
                    args.insert(0, "self")
            else:
                f.write("\n")

            f.write("\n")
            f.write(" " * indent * 4)
            f.write("# noinspection PyUnusedLocal,PyPep8Naming,"
                    "PyMethodMayBeStatic\n")
            f.write(" " * indent * 4)
            f.write("# noinspection PyShadowingBuiltins,PyShadowingNames\n")
            subsequent_indent = indent * 4 + len(tmp_name) + len("def ") + 1
            args = ", ".join(args)
            line = " " * indent * 4
            line += "def {}({}):".format(tmp_name, args)
            f.write(textwrap.fill(line, width=80,
                                  subsequent_indent=" " * subsequent_indent))
            f.write("\n")
            dump_docstring(tmp, f, indent + 1)
            f.write(" " * (indent + 1) * 4)
            f.write("pass\n")
        elif isinstance(tmp, (Object.Object, Map.Map, Archetype.Archetype,
                              Player.Player)):
            instances.append([tmp, tmp_name, doc, indent])
        elif inspect.isclass(obj):
            f.write("\n")
            f.write(" " * indent * 4)
            
            # define the property
            f.write("{} = None;\n".format("_" + tmp_name))
            
            f.write("\n")
            f.write(" " * indent * 4)
            
            f.write("# noinspection PyUnusedLocal,PyPep8Naming,"
                    "PyMethodMayBeStatic\n")
            f.write(" " * indent * 4)
            f.write("@property\n")
            f.write(" " * indent * 4)
            f.write("def {}(self):\n".format(tmp_name, tmp))
            types = dump_docstring(tmp, f, indent + 1, is_getter=True,
                                   obj_name=tmp_name)
            f.write(" " * (indent + 1) * 4)
            f.write("value = getattr(self, {})\n".format(repr("_" + tmp_name)))

            if types is not None:
                f.write(" " * (indent + 1) * 4)
                f.write("assert isinstance(value, ({},))\n".format(
                    ", ".join(types) + ", type(None)"))

            f.write(" " * (indent + 1) * 4)
            f.write("return value\n\n")
            f.write(" " * indent * 4)
            f.write("# noinspection PyUnusedLocal,PyPep8Naming,"
                    "PyMethodMayBeStatic\n")
            f.write(" " * indent * 4)
            f.write("@{}.setter\n".format(tmp_name))
            f.write(" " * indent * 4)
            f.write("def {}(self, value):\n".format(tmp_name, tmp))
            dump_docstring(tmp, f, indent + 1, is_setter=True,
                           obj_name=tmp_name)
            f.write(" " * (indent + 1) * 4)
            f.write("setattr(self, {}, value)\n".format(repr("_" + tmp_name)))
        else:
            subsequent_indent = len(tmp_name) + 4
            line = " " * indent * 4
            line += "{} = {}".format(tmp_name, repr(tmp))
            line = textwrap.fill(line, width=80,
                                 subsequent_indent=" " * subsequent_indent)
            f.write(line)
            f.write("\n")

            parent_name = obj.__name__.replace("Atrinik_", "").upper()
            for x in (tmp_name, parent_name + "_" + tmp_name):
                if x in matches:
                    doc = matches[x]["comment"]
                    break

            if not doc:
                print("Undocumented constant: {}".format(tmp_name))
                doc = tmp_name.replace("_", " ").title()

            dump_docstring(tmp, f, indent, doc=doc)

        names.append(repr(tmp_name))
    
    for imp in imports:
        f.write(imp)

    for ins in instances:
        tmp, tmp_name, doc, indent = ins
        
        f.write(" " * indent * 4)
        # noinspection PyUnresolvedReferences
        f.write("{} = {cls_name}.{cls_name}()\n".format(
            tmp_name, cls_name=tmp.__class__.__name__))

        if not doc:
            doc = tmp_name.replace("_", " ").title()

        dump_docstring(tmp, f, indent, doc=doc)
        
    return names


def main():
    defaults = OrderedDict([
        ("activator", (Object.Object(),
                       "The :class:`~Atrinik.Object.Object` that activated "
                       "the event.")),
        ("pl", (Player.Player(),
                "If the event activator is a player, this will be a :class:"
                "`~Atrinik.Player.Player` instance, otherwise it will be "
                "None.")),
        ("me", (Object.Object(),
                "The :class:`~Atrinik.Object.Object` that has the event object "
                "in its inventory that triggered the event.")),
        ("msg", ("hello",
                 "Message used to activate the event (eg, in case of say "
                 "events). Can be None.")),
    ])

    if not os.path.exists(PATH):
        os.makedirs(PATH)

    with open_doc_file(os.path.join(PATH, "__init__.py")) as f:
        obj = sys.modules["Atrinik"]
        dump_docstring(obj, f)
        names = dump_obj(obj, f, defaults=defaults)
        line = "__all__ = [{}]".format(", ".join(names))
        f.write(textwrap.fill(line, width=80,
                              subsequent_indent=" " * 11))
        f.write("\n")

if not GetSettings()["unit_tests"] and not GetSettings()["plugin_unit_tests"]:
    parser = CParser()
    matches = {}

    def scan(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                matches.update(parser.parse(os.path.join(root, file)))

    scan("src/server")
    scan("src/plugins/plugin_python/include")
    scan("src/include")
    matches.update(parser.parse("../common/toolkit/socket.h"))

    main()
