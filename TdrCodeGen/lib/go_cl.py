#!/usr/bin/env python
# ecoding: utf-8

from core import *

# WChar\WString not implement
TdrType2GoType = {
    TYPE_CHAR: "byte",
    TYPE_INT8: "int8",
    TYPE_UINT8: "uint8",
    TYPE_INT16: "int16",
    TYPE_UINT16: "uint16",
    TYPE_INT32: "int32",
    TYPE_UINT32: "uint32",
    TYPE_INT64: "int64",
    TYPE_UINT64: "uint64",
    TYPE_FLOAT: "float32",
    TYPE_DOUBLE: "float64",
    TYPE_STRING: "string",
    TYPE_BYTE: "byte",
    TYPE_DATETIME: "uint64",
    TYPE_DATE: "uint32",
    TYPE_TIME: "uint32",
    TYPE_IP: "uint32",
}

TdrBaseType = (TYPE_CHAR, TYPE_INT8, TYPE_UINT8, TYPE_INT16, TYPE_UINT16, TYPE_INT32,
               TYPE_UINT32, TYPE_INT64, TYPE_UINT64, TYPE_FLOAT, TYPE_DOUBLE,
               TYPE_BYTE, TYPE_DATETIME, TYPE_DATE, TYPE_TIME, TYPE_IP)


def c_get_type_name(name):
    return c_convert_to_title(name)


def c_get_struct_name(name):
    return c_convert_to_title(name)


def c_get_struct_field_name(name):
    return c_convert_to_title(name)


def c_get_base_version_name(name):
    return c_get_struct_name(name) + "BaseVersion"


def c_get_current_version_name(name):
    return c_get_struct_name(name) + "CurrentVersion"


def c_get_struct_field_version_name(struct_name, field_name):
    return c_get_struct_name(struct_name) + c_get_struct_field_name(field_name) + "Version"


def c_convert_to_title(str):
    result = []
    to_upper = True
    for c in str:
        if c.isalpha():
            if to_upper:
                c = c.upper()
                to_upper = False
        else:
            to_upper = True
        result.append(c)
    return "".join(result)


def c_is_base_type(typeid):
    return typeid in TdrBaseType


def c_is_complex_type(typeid):
    return typeid in (TYPE_STRUCT, TYPE_UNION)


def c_convert_to_go_type(typeid):
    return TdrType2GoType[typeid]


class GoCompiler(TdrCompiler):
    ''' 
    go code compiler 
    author: cowhuang@tencent.com
    '''

    def __init__(self, version, outdir):
        self.version = version
        self.__outdir = outdir
        self.__pkgs = []

    def complete(self):
        import os
        go_tools = {
            "goimports": "golang.org/x/tools/cmd/goimports",
        }
        for _, path in go_tools.items():
            os.system("go get " + path)

        print("goimports & gofmt file")
        for pkg in self.__pkgs:
            outdir = os.path.join(self.__outdir, pkg)
            os.system("goimports -w " + outdir)
            os.system("gofmt -w -s -e " + outdir)

    def __create_code_file(self, path, encoding, *args, **kws):
        if 'encoding' not in kws:
            kws['encoding'] = encoding
        import codecs
        outf = codecs.open(path, 'w', encoding)
        outf.write(render_block('go_file', 0, *args, **kws))
        return outf

    def __create_out(self, metalib):
        # metalib name as pkg name
        pkgname = metalib.namespace
        outdir = os.path.join(self.__outdir, pkgname)
        if not os.path.isdir(outdir):
            os.makedirs(outdir, 0755)
        self.__pkgs.append(pkgname)
        return self.__create_code_file(os.path.join(outdir, metalib.modname + '.go'), metalib.encoding, metalib, pkgname=pkgname, tdrversion=self.version, godoc=self.__doc__)

    def process_metalib(self, metalib):
        outf = self.__create_out(metalib)
        ctx = {'out': outf}
        return ctx

    def process_symbol(self, symdef, ctx):
        sym_blocks = (
            (UnionDef, 'union_code'),
            (StructDef, 'struct_code'),
            # (MacrosGroupDef, 'macros_group'),
            (MacroDef, 'macro'),)

        block = None
        for kls, blk in sym_blocks:
            if isinstance(symdef, kls):
                block = blk
                break
        if not block:
            return
        code = render_block(block, 0, symdef)
        ctx['out'].write(code)

    process_struct = process_symbol
    process_union = process_symbol
    process_macro = process_symbol
    process_macrosgroup = process_symbol
    complete_macrosgroup = process_symbol

# compiler export function
# 每个实际的目标编译模块都需要提供该函数，返回具体的编译实例


def get_compiler(version, outdir, cargs):
    return GoCompiler(version, outdir)
