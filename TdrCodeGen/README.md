TDRCodeGen
=======

# 功能说明

基于TDR2PY，是一款python 开发的 TDR 编译转换工具，根据TDR meta 定义xml文件生成对应语言目标代码。工具按方便扩展方式实现，分离TDR模型处理与具体目标代码生成，内建代码生成模板引擎，无其它依赖，开箱即用。

## 支持语言

- python - by bondshi
- go - by cowhuang
- ... to be continue

## 使用

```
python tdr.py OPTIONS meta-file-path
OPTIONS
    -I incdir: 设置meta定义中 "include" 节点标示文件搜索路径，如果内嵌文件与当前文件在相同目录，则无需设置，重复选项可设置多个搜索路径，ex: -I dir1 dir2
    -C compiler: 设置语言名字，默认为 "python"
    -P params: 设置透传给编译器模块的参数
    -O outdir: 设置输出文件保存目录，默认为当前目录
    -D: debug output

example:
python tdr.py test/demo.xml
```

# 实现说明
## Go
### 生成规则
1. 每个meta的xml定义文件 生成 对应同名的go文件，保存在以metalib名称命名的目录下，作为一个package
1. 变量命名会转换为驼峰
1. macro -> const int32类型
1. macrogroup -> 同macro，增加int别名; 增加名字映射
1. struct -> struct; 嵌套通过 成员变量（对象指针）引用
1. union -> struct；每个成员对应一个对象指针，根据selector初始化指定对象，其他为nil
1. 数组全部转换成slice，为了节省内存提高效率，用户需要自己申请内存；打解包会对长度做判断；Unpack的时候会自动申请slice；
1. 为了兼容go的访问规则，类型名和变量名为驼峰，外部可访问；涉及的字段包括macro<name>, struct/union<name, splittablekey, primarykey, versionindicator, sizeinfo>, entry<name, type, refer, id, select>
1. tcaplus使用到的DB相关字段，index、splittablekey、primarykey会生成一个tdrcom.TDRDBFeilds变量

## Python
### 生成规则 
1. 每个meta 定义文件对应生成同名的python文件，这些python文件保存在以metalib名称命名的目录下，作为一个package；
1. 对于每个macro, 生成同名 python 变量定义；
1. 对于 struct, union，生成同名python class 定义；
1. 数据类型映射规则:
	- 所有整数类型映射为python int；
	- TDR float/double 映射为 python float;
	- TDR string 映射为 python string;
	- TDR char 映射为 python string, 单字符;
	- TDR date 映射为 python datetime.date;
	- TDR time 映射为 python datetime.time;
	- TDR datetime 映射为 python datetime.datetime;
	- TDR ip 映射为4字符string, 与 socket.inet_aton() 返回相同；
	- TDR wchar, wstring 暂不支持;
	- TDR 数组字段映射为 python list;
	
### 映射类
对于 struct/union 节点生成的映射类，会生成如下方法支持序列化操做：

1. pack(cutver = 0, maxsize = 0)
    - 打包，返回buffer.
	- cutver 裁剪版本号，如为0，则按当前版本打包，不进行裁剪；
	- maxsize 设置buf 最大大小，若为0，则设置为结构体最大可能字节数；

2. pack_into(buf, offset = 0, cutver = 0)
	- 打包到指定的buffer，返回新加入到buf中的字节数

3. unpack(buf, offset = 0, cutver = 0)
	从buf 中解包数据，保存到对象对应成员中，返回解包字节数

4. pack_into_dict()
	将对象转化为dict对象（返回值），字段名将会作为dict对象的key，字段值作为value，方便用来与json之类其它表达格式进行转换；

5. unpack_from_dict()
	从dict 对象获取字段值；

### 特别说明
1. python中并无直接与union 对应的类型，为提升性能，并不会对每个union类型的成员创建具体的对象实例，只会根据__init__() 中具体的selector 创建对应的成员实例；
2. 如果 struct 中存在 union 类型成员，则会为其生成包装函数，在首次访问union 成员时，会创建其对象实例，此前需先设置好对应的 selector 字段值；
```
class UnionType:
    def __init__(self, selector):
	    # 只创建selector 对应的成员实例
	    pass
		
class StructType:
    def __init__(self):
        self.selector = 0
        self._union_fld = None

    def union_fld(self):
        if not self._union_fld:
            self._union_fld = UnionType(self.selector)
        return self._union_fld
```
3. 采用python struct 模块进行封包操作，为提升性能，会尽量合并对各个字段pack/unpack 操作，减少python与C 代码之间交互的次数；

### 性能
如果要将tdr2py 生成的代码投入到生产应用，当然需要关心其性能。test目录下提供了一般功能性测试与性能测试代码，执行 ./run_test.sh 可编译并启动python 代码与C++代码的对比测试，
python 代码性能会比C++ 代码低2个量级左右，但对于一般工具和IO密集型的应用，性能已经够用，我们在Web 业务逻辑层使用纯python实现，峰值QPS可达到2K/s，已远高于一般CGI方案。

### 约束

1. 当前不支持 python3

# 扩展 - 更多语言

可以提供编译模块扩展tdr，以便支持其它类型目标语言的生成。具体编译模块代码保存在lib目录下，命名规范为：
- TARGET_cl.py
编译器实现模块文件，具体写法可参考python_cl.py.

- TARGET_proto.py
原型代码模板定义文件，在其中定义目标代码片段，采用bottle 提供的模板渲染引擎（http://bottlepy.org/docs/dev/stpl.html，直接嵌入，无需再下载安装），代码精炼，功能强大.
proto 文件非必须，但一般来讲，采用模板可大大简化目标代码生成，具体写法可参照 python_proto.py.
