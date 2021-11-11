#!/usr/bin/env python
## ecoding: utf-8

# Copyright 2014, Tencent Inc.
# Author: bondshi<bondshi@tencent.com>
# Create: 2014-03-21

import os
from xml.dom import minidom
import re
import logging

TYPE_CHAR = 1
TYPE_INT8 = 2
TYPE_UINT8 = 3
TYPE_INT16 = 4
TYPE_UINT16 = 5
TYPE_INT32 = 6
TYPE_UINT32 = 7
TYPE_INT64 = 8
TYPE_UINT64= 9
TYPE_FLOAT = 10
TYPE_DOUBLE = 11
TYPE_STRING = 12
TYPE_DATE = 14
TYPE_TIME = 15
TYPE_DATETIME = 16
TYPE_IP = 17
TYPE_WCHAR = 18
TYPE_WSTRING = 19
TYPE_BYTE = TYPE_UINT8

TYPE_STRUCT = 100
TYPE_UNION = 101
TYPE_MACRO = 102

CHARSET = 'utf-8'

TDRTYPE_MAP = {
    'char':TYPE_CHAR, 'byte':TYPE_UINT8, 'uchar':TYPE_UINT8,
    'tinyint':TYPE_INT8, 'tinyuint':TYPE_UINT8,
    'smallint':TYPE_INT16, 'smalluint':TYPE_UINT16,
    'short':TYPE_INT16, 'ushort':TYPE_UINT16,
    'int':TYPE_INT32, 'uint':TYPE_UINT32,
    'bigint':TYPE_INT64, 'biguint':TYPE_UINT64,
    'int8':TYPE_INT8, 'uint8':TYPE_UINT8,
    'int16':TYPE_INT16, 'uint16':TYPE_UINT16,
    'int32':TYPE_INT32, 'uint32':TYPE_UINT32,
    'int64':TYPE_INT64, 'uint64':TYPE_UINT64,
    'float':TYPE_FLOAT, 'double':TYPE_DOUBLE,
    'string':TYPE_STRING, 'date':TYPE_DATE,
    'time':TYPE_TIME, 'datetime':TYPE_DATETIME,
    'ip':TYPE_IP,
}

INT_VALUE_TYPES = (TYPE_CHAR, TYPE_UINT8, TYPE_UINT16, TYPE_UINT32, TYPE_UINT64,
                    TYPE_INT8, TYPE_INT16, TYPE_INT32, TYPE_INT64,
                    TYPE_FLOAT, TYPE_DOUBLE)

FIXSIZE_TYPES = {
    TYPE_CHAR:1,
    TYPE_INT8:1, TYPE_UINT8:1,
    TYPE_INT16:2, TYPE_UINT16:2,
    TYPE_INT32:4, TYPE_UINT32:4,
    TYPE_INT64:8, TYPE_UINT64:8,
    TYPE_FLOAT:4, TYPE_DOUBLE:8,
    TYPE_DATE:4, TYPE_TIME:4,
    TYPE_DATETIME:8, TYPE_IP:4,
}


SYM_MACRO = TYPE_MACRO
SYM_STRUCT = TYPE_STRUCT
SYM_UNION = TYPE_UNION

_metalibs = {}
_symbols = {}
_re_number = re.compile('^(-|\+)?(0[xX][0-9A-Fa-f]+|[0-9]+)$')

def _get_constv(sym):
    if not _re_number.match(sym):
        t, m = _get_symbol(sym)
        assert t == SYM_MACRO
        return _get_constv(m.value)
    base = 10
    if sym[:2] in ('0x', '0X'):
        base = 16
    return int(sym, base=base)

def _register_metalib(metalib):
    filename = os.path.basename(metalib.xmlfile)
    if not filename in _metalibs:
        _metalibs[filename] = metalib

def _get_metalib(xmlfile):
    filename = os.path.basename(xmlfile)
    if filename in _metalibs:
        return _metalibs[filename]

def _has_symbol(symname):
    return symname in _symbols

def _add_symbol(symname, symtype, symobj):
    assert symname not in _symbols
    _symbols[symname] = (symtype, symobj)

def _get_symbol(symname):
    'return (type_id, type_obj)'
    return _symbols[symname]

class TdrType(object):
    def __init__(self, typeid):
        self.typeid = typeid

    def __str__(self):
        return 'TdrType:%d' % self.typeid

    __repr__ = __str__

    def check_field_def(self, fld):
        if self.typeid == TYPE_STRING:
            return self.__check_str_def(fld)
        if self.typeid == TYPE_CHAR:
            # CHAR may use macro defaultvalue
            # return self.__check_char_def(fld)
            return

    def is_integer(self):
        return self.typeid in (TYPE_INT8, TYPE_UINT8,
                               TYPE_INT16, TYPE_UINT16,
                               TYPE_INT32, TYPE_UINT32,
                               TYPE_INT64, TYPE_UINT64)
    def is_float(self):
        return self.typeid in (TYPE_FLOAT, TYPE_DOUBLE)

    def __check_str_def(self, fld):
        if not fld.size:
            raise Exception('%s:attribute size absent' % fld)
        if fld.defaultvalue and \
           len(fld.defaultvalue) > (_get_constv(fld.size) - 1):
            raise Exception('%s:too large default value' % fld)

    def __check_char_def(self, fld):
        if fld.defaultvalue and len(fld.defaultvalue) > 1:
            raise Exception('%s:wrong default value' % fld)

def get_typedef(typename):
    def tdr_typeid(typename):
        return TDRTYPE_MAP.get(typename, None)

    ltypename = typename.lower()
    if ltypename in ('wchar', 'wstring'):
        raise Exception('unsupport type:%s' % typename)

    typeid = tdr_typeid(ltypename)
    if typeid:
        return TdrType(typeid)

    typeid, typedef = _get_symbol(typename)
    if typeid in (TYPE_STRUCT, TYPE_UNION):
        return typedef
    else:
        raise Exception('wrong type:%s' % typename)

_xml_getattr = lambda x,k:x.attributes.has_key(k) and x.attributes[k].value.strip() or ''
_macro_map = {}

class MacroDef(object):
    def __init__(self, xmldef):
        xml_getattr = lambda k:_xml_getattr(xmldef, k)
        self.name = xml_getattr('name')
        self.value = xml_getattr('value')
        self.desc = xml_getattr('desc')
        self.value = _macro_map[self.name] = _macro_map.get(self.value, self.value)

class MacrosGroupDef(object):
    def __init__(self, xmldef):
        xml_getattr = lambda k:_xml_getattr(xmldef, k)
        self.name = xml_getattr('name')
        self.desc = xml_getattr('desc')

class StructDef(object):
    typeid = TYPE_STRUCT

    def __init__(self, xmldef):
        self.fields = []
        self.maxsize = 0
        self.minsize = 0
        self.sizeinfo = ""
        self.sizeinfo_list = []
        # DB related fields, bu guan tdr de shi, che dan
        self.splittablekey = ""
        self.primarykey = ""
        self.index_column_map = {}
        self._parse(xmldef)

    def has_field(self, field_name):
        return field_name in [f.name for f in self.fields]

    def get_sub_fields(self, field_name):
        parts = field_name.split('.')
        klass = self
        sub_flds = []

        for part in parts[:-1]:
            flds = filter(lambda f:f.name == part, klass.fields)
            if not flds:
                raise Exception('wrong field name:%s,%s' % (
                    self.name, field_name))
            fld = flds[0]
            sub_flds.append(fld)
            t, klass = _get_symbol(fld.type)
            if t not in (TYPE_UNION, TYPE_STRUCT):
                raise Exception('wrong field name:%s,%s' % (
                    self.name, field_name))
        flds = filter(lambda f:f.name == parts[-1], klass.fields)
        if not flds:
            raise Exception('wrong field name:%s,%s' % (
                self.name, field_name))
        sub_flds.append(flds[0])
        return sub_flds

    def get_field(self, field_name):
        subflds = self.get_sub_fields(field_name)
        if subflds:
            return subflds[-1]

    def get_field_offset(self, fname):
        subflds = self.get_sub_fields(fname)
        offsets = [f.offset for f in subflds]
        if -1 in offsets:
            return -1
        return sum(offsets)

    def check_fix_int_field(self, fname):
        subflds = self.get_sub_fields(fname)
        if not subflds[-1].typedef.is_integer():
            raise Exception('Not a integer field:%s.%s' % (
                self.name, fname))
        if -1 in [fld.offset for fld in subflds]:
            raise Exception('Offset is not fixed:%s.%s' % (
                self.name, fname))

    def _parse(self, xmldef):
        xml_getattr = lambda k:_xml_getattr(xmldef, k)
        self.name = xml_getattr('name')
        if not self.name:
            raise Exception('invalid struct definition, no name:\n%s' % xmldef.toxml())
        logging.info('parse struct:%s' % self.name)
        self.base_version = _get_constv(xml_getattr('version'))
        self.desc = xml_getattr('desc')
        self.versionindicator = xml_getattr("versionindicator")
        self.sizeinfo = xml_getattr("sizeinfo")
        self.splittablekey = xml_getattr("splittablekey")
        self.primarykey = xml_getattr("primarykey")

        self.version = self.base_version
        offset = 0
        for entrydef in xmldef.getElementsByTagName('entry'):
            entry = EntryDef(self, entrydef)
            self.fields.append(entry)
            entry.setup()
            if entry.version > self.version:
                self.version = entry.version
            if isinstance(entry.typedef, StructDef) and \
               entry.typedef.version > self.version:
                self.version = entry.typedef.version

            entry.offset = offset
            if offset != -1:
                if entry.maxsize == entry.minsize:
                    offset += entry.maxsize
                else:
                    offset = -1
            if entry.sizeinfo:
                self.sizeinfo_list.append(entry.sizeinfo)

        # index tag, DB related
        for entrydef in xmldef.getElementsByTagName('index'):
            name = _xml_getattr(entrydef, "name")
            column = _xml_getattr(entrydef, "column")
            if name and column:
                self.index_column_map[name] = column

        if self.versionindicator:
            self.check_fix_int_field(self.versionindicator)

        self.maxsize = sum([f.maxsize for f in self.fields])
        self.minsize = sum([f.minsize for f in self.fields])
        logging.debug("struct version:%s=%s" % (self.name, self.version))


class UnionDef(StructDef):
    typeid = TYPE_UNION

    def __init__(self, xmldef):
        super(UnionDef, self).__init__(xmldef)

    def check_field_def(self, fld):
        if not fld.select:
            raise Exception('%s:union field must has selector' % fld)

        fld_select = fld.structdef.get_field(fld.select)
        if not fld_select or not fld_select.typedef.is_integer():
            raise Exception('%s:wrong select:%s' % (fld, fld.select))

    def _parse(self, xmldef):
        StructDef._parse(self, xmldef)
        selector_map = {}
        for fld in self.fields:
            if not fld.id:
                raise Exception("%s:attribute 'id' absent" % entry)
            select_id = _get_constv(fld.id)
            if select_id in selector_map:
                raise Exception("%s:duplicated union field id:%s" % (fld, fld.id))
            selector_map[select_id] = fld.name
        self.maxsize = max([fld.maxsize for fld in self.fields])
        self.minsize = min([fld.minsize for fld in self.fields])


class EntryDef(object):
    def __init__(self, structdef, xmldef):
        self.offset = 0 # offset in struct layout
        self.structdef = structdef
        self.__parse(xmldef)

    def __str__(self):
        return '%s.%s' % (self.structdef.name, self.name)

    __repr__ = __str__

    @property
    def typeid(self):
        return self.typedef.typeid

    def __parse(self, xmldef):
        structdef = self.structdef
        xml_getattr = lambda k:_xml_getattr(xmldef, k)
        for fld in ('name', 'type', 'defaultvalue', 'sizeinfo', 'refer', 'size',
                    'count', 'version', 'id', 'select', 'desc',
                    'customattr'):
            setattr(self, fld, xml_getattr(fld))

        if not self.name or not self.type:
            raise Exception("%s:wrong field define" %
                            structdef.name)

        self.typedef = get_typedef(self.type)
        if isinstance(self.defaultvalue, unicode):
            self.defaultvalue = self.defaultvalue.encode(CHARSET)

        # if defaultvalue,size,count is macro, replace it
        if self.defaultvalue and self.typeid in INT_VALUE_TYPES:
            if self.defaultvalue in _macro_map:
                self.defaultvalue = _macro_map[self.defaultvalue]
        if self.size and self.size in _macro_map:
            self.size = _macro_map[self.size]
        if self.count and self.count in _macro_map:
            self.count = _macro_map[self.count]

        # customattr: @fval:x1=y1;x2=y2;
        self.fvals = {}
        if self.customattr:
            if self.customattr[:6] != '@fval:':
                logging.warn('%s:ignore unsupport customattr:%s',
                             self, self.customattr)
            elif self.typedef.typeid != TYPE_STRUCT or self.count:
                raise Exception('%s:only struct && not array field support @fval indicator' \
                                % self)
            else:
                self.fvals = self.__parse_fvals(self.customattr[6:])

    def __parse_fvals(self, fvstr):
        fvals = {}
        for f, v in map(lambda x:x.split('='),
                        filter(None, fvstr.split(';'))):
            f, v = f.strip(), v.strip()
            if not self.typedef.has_field(f):
                raise Exception('%s:wrong @fval field:%s' % (self, f))

            ftype = self.typedef.get_field(f).typedef
            if not ftype.is_integer():
                raise Exception('%s:@fval only support integer field:%s' % (self, f))

            try:
                _get_constv(v)
            except:
                raise Exception('%s:@fval value is invalid:%s' % (self, v))
            fvals[f] = v

        return fvals

    def setup(self):
        check_fun = getattr(self.typedef, 'check_field_def', None)
        if check_fun:
            check_fun(self)

        # check & set version
        typedef = self.typedef
        structdef = self.structdef
        self.version = _get_constv(self.version) if self.version else \
                       structdef.base_version
        if self.version < structdef.base_version:
            raise Exception('%s:wrong version:ver=%s,expected>=%s' % (
                self, self.version, structdef.base_version))

        if isinstance(typedef, StructDef) and self.version < typedef.base_version:
            raise Exception('%s:wrong version:ver=%s,expected>=%s' % (
                self, self.version, typedef.base_version))

        # check refer
        if self.refer:
            fld = structdef.get_field(self.refer)
            if not fld or not fld.typedef.is_integer():
                raise Exception("%s:wrong refer:%s" % (self, self.refer))
            if fld.version > self.version:
                raise Exception('%s:wrong version:must <= refer version' % self)

        # check sizeinfo
        if self.sizeinfo:
            if self.sizeinfo[:5] == 'this.':
                self.sizeinfo = self.name + self.sizeinfo[4:]
            structdef.check_fix_int_field(self.sizeinfo)

        # set minsize & maxsize
        if self.typeid in FIXSIZE_TYPES:
            self.maxsize = FIXSIZE_TYPES[self.typeid]
            self.minsize = self.maxsize
        elif self.typeid == TYPE_STRING:
            #pack format: [size(uint)][string (\0)]
            self.maxsize = _get_constv(self.size) + 4
            self.minsize = 5
        elif isinstance(self.typedef, StructDef):
            self.maxsize = self.typedef.maxsize
            self.minsize = self.typedef.minsize
        else:
            assert False

        if self.count:
            self.maxsize = _get_constv(self.count) * self.maxsize
            self.minsize = self.refer and 0 or self.maxsize


class Metalib(object):
    def __init__(self, xmlfile, compiler, incpath=None, ns=None):
        logging.info('convert file to utf8:%s', xmlfile)
        self._convert_xml_to_utf8(xmlfile)
        logging.info('load meta file:%s', xmlfile)
        doc = minidom.parse(xmlfile)
        metalibs = doc.getElementsByTagName("metalib")
        if len(metalibs) != 1:
            raise Exception("<metalib> node number must be 1:%s" % xmlfile)
        self.__metadef = metalibs[0]
        self.__compiler = compiler
        self.__incpath = incpath

        self.xmlfile = xmlfile
        self.namespace = _xml_getattr(self.__metadef, 'name')
        self.version = _xml_getattr(self.__metadef, 'version')
        if not self.namespace:
            self.namespace = ns
        if not self.namespace or not self.version:
            raise Exception('name or version absent:%s' % xmlfile)
        self.modname = os.path.splitext(os.path.basename(xmlfile))[0]
        self.encoding = doc.encoding if doc.encoding else 'utf-8'

    def _convert_xml_to_utf8(self, xmlfile):
        # xml文件转换为utf8编码
        content = ""
        with open(xmlfile, "r") as f:
            encode_pat = re.compile(r'encoding\s*=\s*\"(.*?)\"')
            # find xml encode mark
            content = f.read()
            encode = encode_pat.findall(content)
            encode = encode[0] if encode else None
            if not encode or encode.lower() == "utf-8".lower():
                return
            # replace xml encode mark
            content = re.sub(encode_pat, 'encoding="UTF-8"', content)
            # change file content encode
            content = content.decode(encode).encode("utf-8")
        
        open(xmlfile, "w").close()
        with open(xmlfile, "w") as f:
            f.write(content)

    def compile(self):
        _register_metalib(self)
        ctx = self.__compiler.process_metalib(self)
        for child in self.__metadef.childNodes:
            name = child.localName
            if name in ('macro', 'struct', 'union', 'macrosgroup', 'include'):
                if name != 'include':
                    sym_name = _xml_getattr(child, "name")
                    if _has_symbol(sym_name):
                        raise Exception('duplicated symbol "%s",%s' % (
                            sym_name, self.xmlfile))
                fun = getattr(self, '_Metalib__process_%s' % name)
                fun(child, ctx)
        logging.info('complete metafile:%s', self.xmlfile)
        # endfor

    def __process_macrosgroup(self, node, ctx):
        s = MacrosGroupDef(node)
        start, end = getattr(self.__compiler, 'process_macrosgroup', None), \
                     getattr(self.__compiler, 'complete_macrosgroup', None)
        if start:
            start(s, ctx)
        for child in node.getElementsByTagName('macro'):
            self.__process_macro(child, ctx)
        if end:
            end(s, ctx)

    def __process_macro(self, node, ctx):
        s = MacroDef(node)
        v = s.value
        if not _re_number.match(v):
            try:
                t, m = _get_symbol(v)
                if t != SYM_MACRO:
                    raise Exception('wrong macro define:%s:macro value must '
                                    'be integer or other macro name' % s.name)
            except KeyError:
                raise Exception('wrong macro define:%s:macro value must '
                                'be integer or other macro name' % s.name)
        _add_symbol(s.name, SYM_MACRO, s)
        self.__compiler.process_macro(s, ctx)

    def __process_struct(self, node, ctx):
        s = StructDef(node)
        _add_symbol(s.name, SYM_STRUCT, s)
        self.__compiler.process_struct(s, ctx)

    def __process_union(self, node, ctx):
        s = UnionDef(node)
        _add_symbol(s.name, SYM_UNION, s)
        self.__compiler.process_struct(s, ctx)

    def __process_include(self, node, ctx):
        filename = _xml_getattr(node, "file")
        metalib = _get_metalib(filename)
        if not metalib:
            metalib = Metalib(_get_metafile_full_path(filename, self.__incpath),
                              self.__compiler, self.__incpath,
                              self.namespace)
            if metalib.namespace != self.namespace:
                raise Exception("namespace mismatch:%s(%s) VS %s(%s)" % (
                        metalib.namespace, metalib.xmlfile,
                        self.namespace, self.xmlfile))
            else:
                metalib.compile()
        self.__compiler.process_include(metalib, ctx)

def _get_metafile_full_path(filename, inc_path):
    for path in inc_path:
        filepath = os.path.join(path, filename)
        if os.path.isfile(filepath):
            return filepath
    raise Exception("include file not found:%s" % filename)


#
# bottle template
# http://bottlepy.org/
# Copyright (c) 2013, Marcel Hellkamp.
#
import functools

def touni(s, enc='utf8', err='strict'):
    return s.decode(enc, err) if isinstance(s, bytes) else unicode(s)

class TemplateError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class cached_property(object):
    ''' A property that is only computed once per instance and then replaces
    itself with an ordinary attribute. Deleting the attribute resets the
    property. '''

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None: return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


class BaseTemplate(object):
    """ Base class and minimal API for template adapters """
    extensions = ['tpl','html','thtml','stpl']
    settings = {} #used in prepare()
    defaults = {} #used in render()

    def __init__(self, source=None, name=None, lookup=[], encoding='utf8', **settings):
        """ Create a new template.
        If the source parameter (str or buffer) is missing, the name argument
        is used to guess a template filename. Subclasses can assume that
        self.source and/or self.filename are set. Both are strings.
        The lookup, encoding and settings parameters are stored as instance
        variables.
        The lookup parameter stores a list containing directory paths.
        The encoding parameter should be used to decode byte strings or files.
        The settings parameter contains a dict for engine-specific settings.
        """
        self.name = name
        self.source = source.read() if hasattr(source, 'read') else source
        self.filename = source.filename if hasattr(source, 'filename') else None
        self.lookup = [os.path.abspath(x) for x in lookup]
        self.encoding = encoding
        self.settings = self.settings.copy() # Copy from class variable
        self.settings.update(settings) # Apply
        if not self.source and self.name:
            self.filename = self.search(self.name, self.lookup)
            if not self.filename:
                raise TemplateError('Template %s not found.' % repr(name))
        if not self.source and not self.filename:
            raise TemplateError('No template specified.')
        self.prepare(**self.settings)

    @classmethod
    def search(cls, name, lookup=[]):
        """ Search name in all directories specified in lookup.
        First without, then with common extensions. Return first hit. """
        if not lookup:
            depr('The template lookup path list should not be empty.') #0.12
            lookup = ['.']

        if os.path.isabs(name) and os.path.isfile(name):
            depr('Absolute template path names are deprecated.') #0.12
            return os.path.abspath(name)

        for spath in lookup:
            spath = os.path.abspath(spath) + os.sep
            fname = os.path.abspath(os.path.join(spath, name))
            if not fname.startswith(spath): continue
            if os.path.isfile(fname): return fname
            for ext in cls.extensions:
                if os.path.isfile('%s.%s' % (fname, ext)):
                    return '%s.%s' % (fname, ext)

    @classmethod
    def global_config(cls, key, *args):
        ''' This reads or sets the global settings stored in class.settings. '''
        if args:
            cls.settings = cls.settings.copy() # Make settings local to class
            cls.settings[key] = args[0]
        else:
            return cls.settings[key]

    def prepare(self, **options):
        """ Run preparations (parsing, caching, ...).
        It should be possible to call this again to refresh a template or to
        update settings.
        """
        raise NotImplementedError

    def render(self, *args, **kwargs):
        """ Render the template with the specified local variables and return
        a single byte or unicode string. If it is a byte string, the encoding
        must match self.encoding. This method must be thread-safe!
        Local variables may be provided in dictionaries (args)
        or directly, as keywords (kwargs).
        """
        raise NotImplementedError

class SimpleTemplate(BaseTemplate):

    def prepare(self, escape_func=None, noescape=True, syntax=None, **ka):
        self.cache = {}
        enc = self.encoding
        self._str = lambda x: touni(x, enc)
        # self._escape = lambda x: escape_func(touni(x, enc))
        self._escape = lambda x: touni(x, enc)
        self.syntax = syntax
        if noescape:
            self._str, self._escape = self._escape, self._str

    @cached_property
    def co(self):
        return compile(self.code, self.filename or '<string>', 'exec')

    @cached_property
    def code(self):
        source = self.source or open(self.filename, 'rb').read()
        try:
            source, encoding = touni(source), 'utf8'
        except UnicodeError:
            depr('Template encodings other than utf8 are no longer supported.') #0.11
            source, encoding = touni(source, 'latin1'), 'latin1'
        parser = StplParser(source, encoding=encoding, syntax=self.syntax)
        code = parser.translate()
        self.encoding = parser.encoding
        return code

    def _rebase(self, _env, _name=None, **kwargs):
        if _name is None:
            depr('Rebase function called without arguments.'
                 ' You were probably looking for {{base}}?', True) #0.12
        _env['_rebase'] = (_name, kwargs)

    def _include(self, _env, _name=None, **kwargs):
        if _name is None:
            depr('Rebase function called without arguments.'
                 ' You were probably looking for {{base}}?', True) #0.12
        env = _env.copy()
        env.update(kwargs)
        if _name not in self.cache:
            self.cache[_name] = self.__class__(name=_name, lookup=self.lookup)
        return self.cache[_name].execute(env['_stdout'], env)

    def execute(self, _stdout, kwargs):
        env = self.defaults.copy()
        env.update(kwargs)
        env.update({'_stdout': _stdout, '_printlist': _stdout.extend,
            'include': functools.partial(self._include, env),
            'rebase': functools.partial(self._rebase, env), '_rebase': None,
            '_str': self._str, '_escape': self._escape, 'get': env.get,
            'setdefault': env.setdefault, 'defined': env.__contains__ })

        eval(self.co, env)
        if env.get('_rebase'):
            subtpl, rargs = env.pop('_rebase')
            rargs['base'] = ''.join(_stdout) #copy stdout
            del _stdout[:] # clear stdout
            return self._include(env, subtpl, **rargs)
        return env

    def render(self, env):
        """ Render the template using keyword arguments as local variables. """
        stdout = []
        self.execute(stdout, env)
        return ''.join(stdout)


class StplSyntaxError(TemplateError): pass


class StplParser(object):
    ''' Parser for stpl templates. '''
    _re_cache = {} #: Cache for compiled re patterns
    # This huge pile of voodoo magic splits python code into 8 different tokens.
    # 1: All kinds of python strings (trust me, it works)
    _re_tok = '((?m)[urbURB]?(?:\'\'(?!\')|""(?!")|\'{6}|"{6}' \
               '|\'(?:[^\\\\\']|\\\\.)+?\'|"(?:[^\\\\"]|\\\\.)+?"' \
               '|\'{3}(?:[^\\\\]|\\\\.|\\n)+?\'{3}' \
               '|"{3}(?:[^\\\\]|\\\\.|\\n)+?"{3}))'
    _re_inl = _re_tok.replace('|\\n','') # We re-use this string pattern later
    # 2: Comments (until end of line, but not the newline itself)
    _re_tok += '|(#.*)'
    # 3,4: Keywords that start or continue a python block (only start of line)
    _re_tok += '|^([ \\t]*(?:if|for|while|with|try|def|class)\\b)' \
               '|^([ \\t]*(?:elif|else|except|finally)\\b)'
    # 5: Our special 'end' keyword (but only if it stands alone)
    _re_tok += '|((?:^|;)[ \\t]*end[ \\t]*(?=(?:%(block_close)s[ \\t]*)?\\r?$|;|#))'
    # 6: A customizable end-of-code-block template token (only end of line)
    _re_tok += '|(%(block_close)s[ \\t]*(?=$))'
    # 7: And finally, a single newline. The 8th token is 'everything else'
    _re_tok += '|(\\r?\\n)'
    # Match the start tokens of code areas in a template
    _re_split = '(?m)^[ \t]*(\\\\?)((%(line_start)s)|(%(block_start)s))(%%?)'
    # Match inline statements (may contain python strings)
    _re_inl = '%%(inline_start)s((?:%s|[^\'"\n]*?)+)%%(inline_end)s' % _re_inl

    default_syntax = '<% %> % {{ }}'

    def __init__(self, source, syntax=None, encoding='utf8'):
        self.source, self.encoding = touni(source, encoding), encoding
        self.set_syntax(syntax or self.default_syntax)
        self.code_buffer, self.text_buffer = [], []
        self.lineno, self.offset = 1, 0
        self.indent, self.indent_mod = 0, 0

    def get_syntax(self):
        ''' Tokens as a space separated string (default: <% %> % {{ }}) '''
        return self._syntax

    def set_syntax(self, syntax):
        self._syntax = syntax
        self._tokens = syntax.split()
        if not syntax in self._re_cache:
            names = 'block_start block_close line_start inline_start inline_end'
            etokens = map(re.escape, self._tokens)
            pattern_vars = dict(zip(names.split(), etokens))
            patterns = (self._re_split, self._re_tok, self._re_inl)
            patterns = [re.compile(p%pattern_vars) for p in patterns]
            self._re_cache[syntax] = patterns
        self.re_split, self.re_tok, self.re_inl = self._re_cache[syntax]

    syntax = property(get_syntax, set_syntax)

    def translate(self):
        if self.offset: raise RuntimeError('Parser is a one time instance.')
        while True:
            m = self.re_split.search(self.source[self.offset:])
            if m:
                text = self.source[self.offset:self.offset+m.start()]
                self.text_buffer.append(text)
                self.offset += m.end()
                if m.group(1): # New escape syntax
                    line, sep, _ = self.source[self.offset:].partition('\n')
                    self.text_buffer.append(m.group(2)+m.group(5)+line+sep)
                    self.offset += len(line+sep)+1
                    continue
                elif m.group(5): # Old escape syntax
                    depr('Escape code lines with a backslash.') #0.12
                    line, sep, _ = self.source[self.offset:].partition('\n')
                    self.text_buffer.append(m.group(2)+line+sep)
                    self.offset += len(line+sep)+1
                    continue
                self.flush_text()
                self.read_code(multiline=bool(m.group(4)))
            else: break
        self.text_buffer.append(self.source[self.offset:])
        self.flush_text()
        return ''.join(self.code_buffer)

    def read_code(self, multiline):
        code_line, comment = '', ''
        while True:
            m = self.re_tok.search(self.source[self.offset:])
            if not m:
                code_line += self.source[self.offset:]
                self.offset = len(self.source)
                self.write_code(code_line.strip(), comment)
                return
            code_line += self.source[self.offset:self.offset+m.start()]
            self.offset += m.end()
            _str, _com, _blk1, _blk2, _end, _cend, _nl = m.groups()
            if code_line and (_blk1 or _blk2): # a if b else c
                code_line += _blk1 or _blk2
                continue
            if _str:    # Python string
                code_line += _str
            elif _com:  # Python comment (up to EOL)
                comment = _com
                if multiline and _com.strip().endswith(self._tokens[1]):
                    multiline = False # Allow end-of-block in comments
            elif _blk1: # Start-block keyword (if/for/while/def/try/...)
                code_line, self.indent_mod = _blk1, -1
                self.indent += 1
            elif _blk2: # Continue-block keyword (else/elif/except/...)
                code_line, self.indent_mod = _blk2, -1
            elif _end:  # The non-standard 'end'-keyword (ends a block)
                self.indent -= 1
            elif _cend: # The end-code-block template token (usually '%>')
                if multiline: multiline = False
                else: code_line += _cend
            else: # \n
                self.write_code(code_line.strip(), comment)
                self.lineno += 1
                code_line, comment, self.indent_mod = '', '', 0
                if not multiline:
                    break

    def flush_text(self):
        text = ''.join(self.text_buffer)
        del self.text_buffer[:]
        if not text: return
        parts, pos, nl = [], 0, '\\\n'+'  '*self.indent
        for m in self.re_inl.finditer(text):
            prefix, pos = text[pos:m.start()], m.end()
            if prefix:
                parts.append(nl.join(map(repr, prefix.splitlines(True))))
            if prefix.endswith('\n'): parts[-1] += nl
            parts.append(self.process_inline(m.group(1).strip()))
        if pos < len(text):
            prefix = text[pos:]
            lines = prefix.splitlines(True)
            if lines[-1].endswith('\\\\\n'): lines[-1] = lines[-1][:-3]
            elif lines[-1].endswith('\\\\\r\n'): lines[-1] = lines[-1][:-4]
            parts.append(nl.join(map(repr, lines)))
        code = '_printlist((%s,))' % ', '.join(parts)
        self.lineno += code.count('\n')+1
        self.write_code(code)

    def process_inline(self, chunk):
        if chunk[0] == '!': return '_str(%s)' % chunk[1:]
        return '_escape(%s)' % chunk

    def write_code(self, line, comment=''):
        line, comment = self.fix_backward_compatibility(line, comment)
        code  = '  ' * (self.indent+self.indent_mod)
        code += line.lstrip() + comment + '\n'
        self.code_buffer.append(code)

    def fix_backward_compatibility(self, line, comment):
        parts = line.strip().split(None, 2)
        if parts and parts[0] in ('include', 'rebase'):
            depr('The include and rebase keywords are functions now.') #0.12
            if len(parts) == 1:   return "_printlist([base])", comment
            elif len(parts) == 2: return "_=%s(%r)" % tuple(parts), comment
            else:                 return "_=%s(%r, %s)" % tuple(parts), comment
        if self.lineno <= 2 and not line.strip() and 'coding' in comment:
            m = re.match(r"#.*coding[:=]\s*([-\w.]+)", comment)
            if m:
                depr('PEP263 encoding strings in templates are deprecated.') #0.12
                enc = m.group(1)
                self.source = self.source.encode(self.encoding).decode(enc)
                self.encoding = enc
                return line, comment.replace('coding','coding*')
        return line, comment


_templates = {}
def template(tpl, env):
    '''
    Get a rendered template as a string iterator.
    You can use a name, a filename or a template string as first parameter.
    Template rendering arguments can be passed as dictionaries
    or directly (as keyword arguments).
    '''
    adapter = SimpleTemplate
    tplid = id(tpl)
    if tplid not in _templates:
        _templates[tplid] = adapter(source=tpl)
    return _templates[tplid].render(env)


class MapChain(object):
    def __init__(self, *args, **kws):
        self.__maps = [{'_context_':self}]
        if args:
            self.__maps += args
        if kws:
            self.__maps.append(kws)

    def __getitem__(self, key):
        for m in self.__maps:
            if isinstance(m, (dict, MapChain)):
                if key in m:
                    return m[key]
            else:
                try:
                    return getattr(m, key)
                except:
                    pass
        raise KeyError(key)

    def __contains__(self, key):
        for m in self.__maps:
            if isinstance(m, (dict, MapChain)):
                if m.__contains__(key):
                    return True
            elif key in dir(m):
                return True
        return False

    def __str__(self):
        return str(self.__maps)

    def keys(self):
        allkeys = []
        for m in self.__maps:
            if isinstance(m, (dict, MapChain)):
                allkeys += m.keys()
            else:
                allkeys += filter(lambda x:x[0] != '_', dir(m))
        return set(allkeys)

    def sorted_keys(self):
        v = list(self.keys())
        v.sort()
        return v


_global_context = None

def render_code(code_tmpl, indent = 0, *maps, **kws):
    args = []
    if kws:
        args.append(kws)

    if maps:
        args += maps

    if _global_context:
        args.append(_global_context)
    mc = MapChain(*args)
    code = template(code_tmpl, mc)
    if indent == 0:
        return code
    code = re.sub('^', ' ' * indent, code, flags=re.M)
    return re.sub('^\s+$', '', code, flags=re.M)


_blocks = {}
def _get_block(block_id):
    return _blocks[block_id]

def parse_code_proto(path):
    import re
    blk_beg = re.compile('^\s*#@\s*block:\s*(\w+).*$')
    blk_end = re.compile('^\s*#@\s*endblock[^\w]*$')
    blk_py = re.compile('^\s*%')

    block_id = ''
    lines = []
    in_py = False

    def commit_block(block_id, lines):
        _blocks[block_id] = ''.join(lines)

    for line in open(path, 'rt'):
        if block_id:
            if blk_end.match(line):
                commit_block(block_id, lines)
                block_id = ''
                lines = []
            else:
                if not in_py:
                    in_py = blk_py.match(line)
                if in_py:
                    # 多行python code合并为一行
                    if line[-2:] == '\\\n' or line[-3:] == '\\\r\n':
                        line = line.strip()[:-1]
                    else:
                        in_py = False
                lines.append(line)
        else:
            m = blk_beg.match(line)
            if m:
                block_id = m.groups()[0]
                logging.debug('match:%s', m.groups())
            # end
        # end
    # end
    if block_id:
        commit_block(block_id, lines)

def render_block(block_id, indent = 0, *args, **kvs):
    logging.debug('render_block:%s', block_id)
    block_code = _get_block(block_id)
    return render_code(block_code, indent, *args, **kvs)

# c_* 函数可以在模板代码中直接调用
c_render_block = render_block
c_render_code = render_code
c_default = lambda v,d:v if v else d
c_get_constv = _get_constv

def c_escapestr(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")


def _make_global_context(cmod):
    def check_item(k):
        return k.isupper() or \
            k in ('MacroDef', 'MacrosGroupDef', 'StructDef',
                  'UnionDef', 'EntryDef', 'Metalib') or \
            k[:2] == 'c_'

    ctx = dict(filter(lambda x:check_item(x[0]), globals().iteritems()))
    for k in filter(check_item, dir(cmod)):
        ctx[k] = getattr(cmod, k)

    return ctx


def setup_compiler(cname, version, outdir = '', cargs = None):
    import importlib
    cmod = importlib.import_module("{0}_cl".format(cname))

    cdir = os.path.dirname(os.path.realpath(cmod.__file__))
    proto_file = os.path.join(cdir, '%s_proto.py' % cname)
    if os.path.isfile(proto_file):
        logging.info('load code proto:%s', proto_file)
        parse_code_proto(proto_file)
    else:
        logging.debug('proto file not found:%s', proto_file)

    cl = cmod.get_compiler(version, outdir, cargs)
    global _global_context
    _global_context = _make_global_context(cmod)

    return cl


class TdrCompiler(object):
    ''' tdr compiler class prototype
    具体的编译器模块通过提供下面的函数返回具体的TdrCompiler 类实例

    def get_compiler(version, outdir, cargs):
        # version: tdr版本号
        # outdir: 目标文件输出根目录
        # cargs: 通过命令行 '-C arg1 -C arg2' 参数传递给编译模块的参数[arg1, arg2, ...]
        return ConcreteTdrCompiler()
    '''
    def process_metalib(self, metalib):
        '''called when start process one metalib file
        metalib Metalib object
        return one context for other process_* functions
        '''
        ctx = {}
        return ctx

    def complete(self):
        ''' called when compile completed
        '''
        pass

    def process_struct(self, structdef, ctx):
        ''' called when got one struct node
        structdef StructDef object
        ctx  process context data returned by process_metalib
        '''
        pass

    def process_union(self, uniondef, ctx):
        ''' called when got one union node
        uniondef UnionDef object
        ctx  process context data returned by process_metalib
        '''
        pass

    def process_macro(self, macrodef, ctx):
        ''' called when got one macro node
        macrodef MacroDef object
        ctx  process context data returned by process_metalib
        '''
        pass

    def process_macrosgroup(self, macrosgroupdef, ctx):
        ''' called when got one macrosgroup node
        macrosgroupdef MacrosGroupDef object
        ctx  process context data returned by process_metalib
        '''
        pass

    def complete_macrosgroup(self, macrosgroupdef, ctx):
        ''' called when ending one macrosgroup node
        macrosgroupdef MacrosGroupDef object
        ctx  process context data returned by process_metalib
        '''
        pass

    def process_include(self, metalib, ctx):
        ''' called when one included meta file processed
        metalib Metalib object of included metafile
        ctx  process context data returned by process_metalib
        '''
        pass
