#!/usr/bin/env python
## ecoding: utf-8

# Copyright 2014, Tencent Inc.
# Author: bondshi<bondshi@tencent.com>
# Create: 2014-03-21

from core import *

PY_PACK_GROUP_MERGE = 1
PY_PACK_GROUP_ALONE = 2

def c_grouping_pack_flds(fields):
    '''对可以合并进行pack的字段分组，原则：
    1. struct, union, string 成员单独一组 (PY_PACK_GROUP_ALONE)
    2. array 成员单独一组 (PY_PACK_GROUP_ALONE)
    3. 其余version 相同成员合成一组 (PY_PACK_GROUP_MERGE)
    '''
    groups = []
    gtype = 0
    ver = 0
    flds = []

    def _commit_group(gtype, ver, flds):
        if gtype != 0:
            groups.append((gtype, ver, flds))

    commit_group = lambda:_commit_group(gtype, ver, flds)

    for fld in fields:
        if fld.version != ver or gtype != PY_PACK_GROUP_MERGE:
            commit_group()
            gtype, ver, flds = 0, 0, []

        if fld.count or fld.typeid in (TYPE_STRUCT, TYPE_UNION, TYPE_STRING):
            commit_group()
            gtype, ver, flds = PY_PACK_GROUP_ALONE, fld.version, [fld]
        elif gtype == 0:
            gtype, ver, flds = PY_PACK_GROUP_MERGE, fld.version, [fld]
        else:
            flds.append(fld)

    commit_group()
    return groups

PY_PACKINFO_PRIMARY_TYPE = {
    TYPE_CHAR:'c',
    TYPE_INT8:'b', TYPE_UINT8:'B',
    TYPE_INT16:'h', TYPE_UINT16:'H',
    TYPE_INT32:'i', TYPE_UINT32:'I',
    TYPE_INT64:'q', TYPE_UINT64:'Q',
    TYPE_FLOAT:'f', TYPE_DOUBLE:'d',
}

PY_PACKINFO_DATETIME = {
    TYPE_TIME:('I', 'tdr_time2int({{var}})',
               '[tdr_time2int(x) for x in {{var}}]',
               'tdr_int2time({{var}})'),
    TYPE_DATE:('I', 'tdr_date2int({{var}})',
               '[tdr_date2int(x) for x in {{var}}]',
               'tdr_int2date({{var}})'),
    TYPE_DATETIME:('Q', 'tdr_datetime2int({{var}})',
                   '[tdr_datetime2int(x) for x in {{var}}]',
                   'tdr_int2datetime({{var}})'),
}

PY_PACKINFO_IP = {
    TYPE_IP:('4s', '{{var}}[::-1]'),
}


def c_py_get_merge_pack_info(flds):
    def get_pack_info(tid):
        # (fmt, args, size, expr)
        if tid in PY_PACKINFO_PRIMARY_TYPE:
            return (PY_PACKINFO_PRIMARY_TYPE[tid],
                    FIXSIZE_TYPES[tid],
                    '{{var}}')
        elif tid in PY_PACKINFO_DATETIME:
            pk_info = PY_PACKINFO_DATETIME[tid]
            return (pk_info[0],
                    FIXSIZE_TYPES[tid],
                    pk_info[1])
        elif tid in PY_PACKINFO_IP:
            pk_info = PY_PACKINFO_IP[tid]
            return (pk_info[0], FIXSIZE_TYPES[tid],
                    pk_info[1])
        else:
            assert False

    pack_fmt, pack_size, pack_flds = '', 0, []
    for f in flds:
        fmt, size, expr = get_pack_info(f.typeid)
        pack_fmt += fmt
        pack_size += size
        expr = render_code(expr, var='self.'+f.name, size=f.size)
        pack_flds.append(expr)

    return pack_fmt, pack_size, ','.join(pack_flds)


def c_py_get_merge_unpack_info(flds):
    ''' return (fmt, size, form1, form2)
form1 = struct.unpack_from(fmt, buf, offset)
self.f1 = fun(tmp_f1)
...
'''
    fmt, size = '', 0
    form1, form2 = [], []

    for f in flds:
        tid = f.typeid
        if tid in PY_PACKINFO_PRIMARY_TYPE:
            fmt += PY_PACKINFO_PRIMARY_TYPE[tid]
            size += FIXSIZE_TYPES[tid]
            form1.append('self.' + f.name)
        elif tid in PY_PACKINFO_IP:
            pkinfo = PY_PACKINFO_IP[tid]
            fmt += pkinfo[0]
            size += FIXSIZE_TYPES[tid]
            form1.append('tmp_' + f.name)
            form2.append('self.%s = %s' % (
                f.name, render_code(pkinfo[1], var='tmp_' + f.name)))
        elif tid in PY_PACKINFO_DATETIME:
            pkinfo = PY_PACKINFO_DATETIME[tid]
            fmt += pkinfo[0]
            size += FIXSIZE_TYPES[tid]
            form1.append('tmp_' + f.name)
            form2.append('self.%s = %s' % (
                f.name, render_code(pkinfo[3], var='tmp_' + f.name)))
        else:
            logging.error("not plain field:%s", f)
            assert False

    if len(form1) == 1:
        form1.append('')

    return fmt, size, ','.join(form1), '\n'.join(form2)


class PyCompiler(TdrCompiler):
    ''' python code compiler
    '''
    def __init__(self, version, outdir):
        self.version = version
        self.__outdir = outdir
        self.__pkgs = []

    def process_metalib(self, metalib):
        outf = self.__create_out(metalib)
        ctx = {'out':outf}
        return ctx

    def complete(self):
        encoding = 'utf-8'
        for pkg in set(self.__pkgs):
            pkginit = os.path.join(self.__outdir, pkg, '__init__.py')
            self.__create_code_file(pkginit, encoding,
                                    filename='__init__.py')

    def process_symbol(self, symdef, ctx):
        sym_blocks = (
            (UnionDef, 'union_code'),
            (StructDef, 'struct_code'),
            (MacrosGroupDef, 'macros_group'),
            (MacroDef, 'macro'),
            (Metalib, 'import_lib'))

        block = None
        for kls, blk in sym_blocks:
            if isinstance(symdef, kls):
                block = blk
                break
        if not block:
            raise Exception('wrong symbol def:%s' % symdef)
        code = render_block(block, 0, symdef)
        ctx['out'].write(code)


    process_struct = process_symbol
    process_union = process_symbol
    process_macro = process_symbol
    process_macrosgroup = process_symbol
    process_include = process_symbol

    def complete_macrosgroup(self, macgroupdef, ctx):
        pass

    def __create_code_file(self, path, encoding, *args, **kws):
        if 'encoding' not in kws:
            kws['encoding'] = encoding
        import codecs
        outf = codecs.open(path, 'w', encoding)
        outf.write(render_block('python_file', 0, *args, **kws))
        return outf

    def __create_out(self, metalib):
        pkgname = metalib.namespace
        outdir = os.path.join(self.__outdir, pkgname)
        if not os.path.isdir(outdir):
            os.makedirs(outdir, 0755)
        self.__pkgs.append(pkgname)
        return self.__create_code_file(os.path.join(outdir, metalib.modname + '.py'), metalib.encoding, metalib)


c_gen_spec = False

# compiler export function
# 每个实际的目标编译模块都需要提供该函数，返回具体的编译实例
def get_compiler(version, outdir, cargs):
    gen_spec = cargs.get('gen_spec', '').lower()
    if gen_spec in ('y', 'yes', '1', 'true'):
        global c_gen_spec
        c_gen_spec = True

    return PyCompiler(version, outdir)
