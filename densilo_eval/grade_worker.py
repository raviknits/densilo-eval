"""Runs only inside a resource-limited child process. No model credentials."""
import ast
import copy
import json
import resource
import sys

resource.setrlimit(resource.RLIMIT_CPU,(2,2))
resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
try:resource.setrlimit(resource.RLIMIT_AS,(512*1024*1024,512*1024*1024))
except (ValueError,OSError):pass


def grade_code(code, fn, cases):
    if len(code)>20000:raise ValueError('code too long')
    tree=ast.parse(code)
    forbidden=(ast.Import,ast.ImportFrom,ast.ClassDef,ast.Global,ast.Nonlocal,ast.AsyncFunctionDef,ast.With,ast.AsyncWith)
    for node in ast.walk(tree):
        if isinstance(node,forbidden):raise ValueError('unsupported syntax')
        if isinstance(node,ast.Attribute) and node.attr.startswith('_'):raise ValueError('private attributes forbidden')
        if isinstance(node,ast.Name) and node.id.startswith('__'):raise ValueError('dunder names forbidden')
        if isinstance(node,ast.FunctionDef) and node.decorator_list:raise ValueError('decorators forbidden')
    safe={'sum':sum,'min':min,'max':max,'len':len,'range':range,'enumerate':enumerate,'zip':zip,'sorted':sorted,'reversed':reversed,'list':list,'dict':dict,'set':set,'tuple':tuple,'int':int,'str':str,'bool':bool,'float':float,'abs':abs,'all':all,'any':any,'isinstance':isinstance,'Exception':Exception,'ValueError':ValueError,'NotImplementedError':NotImplementedError}
    namespace={'__builtins__':safe};exec(compile(tree,'<submission>','exec'),namespace)
    f=namespace[fn];passed=0
    for args,expected in cases:
        args=copy.deepcopy(args);before=copy.deepcopy(args)
        got=f(*args)
        # Boolean identity matters for access checks; input mutation is forbidden.
        ok=got==expected and (not isinstance(expected,bool) or type(got) is bool) and args==before
        passed+=int(ok)
    return {'success':passed==len(cases),'checks_passed':passed,'checks_total':len(cases)}

if __name__=='__main__':
    try:result=grade_code(**json.load(sys.stdin))
    except Exception as exc:result={'success':False,'reason':type(exc).__name__}
    print(json.dumps(result))
