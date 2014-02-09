#!/usr/bin/python

import ast, _ast, sys

imports = []
funVars = []
symTab = []
classes = []
inbuilts = ["input", "range", "raw_input", "str", "xrange"]

funMode = False
expCall = False
func = ""

debug_notification = "**** Medusa Notification ****"
debug_warning = "**** Medusa Warning ****"
debugging_message = "**** Medusa Debug ****"
debug_error = "**** Medusa Error ****"

operators = dict()
operators['_ast.Add'] = " + "
operators['_ast.Sub'] = " - "
operators['_ast.Mult'] = " * "
operators['_ast.Div'] = " ~/ "
operators['_ast.RShift'] = " >> "
operators['_ast.LShift'] = " << "
operators['_ast.BitAnd'] = " & "
operators['_ast.BitXor'] = " ^ "
operators['_ast.BitOr'] = " | "
operators['_ast.Mod'] = " % "
operators['_ast.Eq'] = " == "
operators['_ast.Gt'] = " > "
operators['_ast.GtE'] = " >= "
operators['_ast.Lt'] = " < "
operators['_ast.LtE'] = " <= "
operators['_ast.NotEq'] = " != "

outFile = open("out.dart", 'w')
code = " void main() {"

class MyParser(ast.NodeVisitor):
    def __init__(self):
        pass

    def parse(self, code):
        tree = ast.parse(code)
        self.visit(tree)

    def escape(self, s):
        s = s.replace('\\', '\\\\')
        s = s.replace('\n', r'\n')
        s = s.replace('\t', r'\t')
        s = s.replace('\r', r'\r')

        return s

    def addImport(self, module):
        global imports

        if imports.__contains__(module) == False:
            imports.append(module)

    def attrHandle(self, stmt_call):
        resolved = ""

        if hasattr(stmt_call, "args"):
            if stmt_call.func.value.id == "self":
                obj = "this"
            else:
                obj = stmt_call.func.value.id

            resolved += " " + obj + "." + stmt_call.func.attr + "("

            alen = len(stmt_call.args)
            i = 0

            while (i < alen):
                if isinstance(stmt_call.args[i], _ast.Num):
                    resolved += str(stmt_call.args[i].n)
                elif isinstance(stmt_call.args[i], _ast.Str):
                    resolved += "'" + stmt_call.args[i].s + "'"
                elif isinstance(stmt_call.args[i], _ast.List):
                    resolved += self.parseList(stmt_call.args[i].elts)
                elif isinstance(stmt_call.args[i], _ast.Name):
                    resolved += stmt_call.args[i].id
                elif isinstance(stmt_call.args[i], _ast.BinOp):
                    resolved += self.parseExp(stmt_call.args[i])
                elif isinstance(stmt_call.args[i], _ast.Call):
                    self.visit_Call(stmt_call.args[i], True)

                if (i + 1) < alen:
                    resolved += ", "
                i += 1

            resolved += ")"

        else:
            if stmt_call.value.id == "self":
                obj = "this"
            else:
                obj = stmt_call.value.id

            resolved = " " + obj + "." + stmt_call.attr

        return resolved

    def parseList(self, theList):
        global func, expCall

        strList = "["
        i = 0
        l = len(theList)

        while i < l:
            item = theList[i]

            if isinstance(item, _ast.Num):
                v = item.n
            elif isinstance(item, _ast.Name):
                v = item.id
            elif isinstance(item, _ast.Str):
                v = "'" + item.s + "'"
            elif isinstance(item, _ast.List):
                v = self.parseList(item.elts)
            elif isinstance(item, _ast.BinOp):
                v = self.parseExp(item)
            elif isinstance(item, _ast.Call):
                expCall = True
                self.visit_Call(item, True)
                expCall = False
                v = func
                func = ""

            strList += str(v)
            if (i + 1) < l:
                strList += ", "
            i += 1

        strList += "]"
        return strList

    def parseExp(self, expr):
        global expCall, func
        powFlag = False

        exp = ""

        if isinstance(expr.left, _ast.Call):
            expCall = True
            self.visit_Call(expr.left, True)
            expCall = False
            exp += func
            func = ""
        else:
            if isinstance(expr.left, _ast.BinOp):
                exp += self.parseExp(expr.left)
            else:
                if isinstance(expr.left, _ast.Num):
                    exp += str(expr.left.n)
                elif isinstance(expr.left, _ast.Name):
                    exp += str(expr.left.id)
                elif isinstance(expr.left, _ast.Str):
                    exp += "'" + str(expr.left.s) + "'"
                elif isinstance(expr.left, _ast.Attribute):
                    exp += self.attrHandle(expr.left)

        op = str(type(expr.op))[8:-2]
        if op in operators:
            exp += operators[op]
        elif isinstance(expr.op, _ast.Pow):
            self.addImport('dart:math')
            exp = "pow (" + exp
            exp += ", "
            powFlag = True
        else:
            print debug_warning
            print "Operator not implemented => " + op
            exit(1)

        if isinstance(expr.right, _ast.Call):
            expCall = True
            self.visit_Call(expr.right, True)
            expCall = False
            exp += func
            func = ""
        else:
            if isinstance(expr.right, _ast.BinOp):
                exp += self.parseExp(expr.right)
            else:
                if isinstance(expr.right, _ast.Num):
                    exp += str(expr.right.n)
                elif isinstance(expr.right, _ast.Name):
                    exp += str(expr.right.id)
                elif isinstance(expr.right, _ast.Str):
                    exp += "'" + str(expr.right.s) + "'"
                elif isinstance(expr.right, _ast.Attribute):
                    exp += self.attrHandle(expr.right)
        if powFlag:
            exp += ")"

        return "(" + exp + ")" #Saxx

    def subscriptHandle(self, stmt_Subscript):
        if str(type(stmt_Subscript.slice))[13:-2] == "Index":
            if str(type(stmt_Subscript.value))[13:-2] == "Subscript":
                data = self.subscriptHandle(stmt_Subscript.value)
            elif str(type(stmt_Subscript.value))[13:-2] == "Name":
                data = str(stmt_Subscript.value.id)
            else:
                print debug_warning
                print "type not supported yet => ", str(type(stmt_Subscript.value))
                exit(1)
            if str(type(stmt_Subscript.slice.value))[13:-2] == "Num":
                num = stmt_Subscript.slice.value.n
                if num < 0:
                    if str(type(stmt_Subscript.value))[13:-2] == "Subscript":
                        data += "[" + self.subscriptHandle(stmt_Subscript.value) + ".length " + str(num) +" ]"
                    elif str(type(stmt_Subscript.value))[13:-2] == "Name":
                        data += "[" + stmt_Subscript.value.id + ".length" + str(num) + "]"
                    else:
                        print debug_warning
                        print "Type not supported => ", str(type(stmt_Subscript.value))
                        exit(1)
                else:
                    data += "[" + str(stmt_Subscript.slice.value.n) + "]"
            elif str(type(stmt_Subscript.slice.value))[13:-2] == "Name":
                data += "[" + stmt_Subscript.slice.value.id + "]"
            else:
                print debug_warning
                print "Type not recognized => ", type(stmt_Subscript.slice.value)
                exit(1)
        elif str(type(stmt_Subscript.slice))[13:-2] == "Slice":
            self.addImport('lib/slice.dart')

            if str(type(stmt_Subscript.value))[13:-2] == "Subscript":
                data = "slice(" + self.subscriptHandle(stmt_Subscript.value) + ", "
            elif str(type(stmt_Subscript.value))[13:-2] == "Name":
                data = "slice(" + stmt_Subscript.value.id + ", "
            else:
                print debug_warning
                print "type not supported yet => ", str(type(stmt_Subscript.value))
                exit(1)
            if isinstance(stmt_Subscript.slice.lower, _ast.Num):
                data += str(stmt_Subscript.slice.lower.n) + ", "
            elif stmt_Subscript.slice.lower == None:
                if stmt_Subscript.slice.step.n < 0:
                    if str(type(stmt_Subscript.value))[13:-2] == "Subscript":
                        data += self.subscriptHandle(stmt_Subscript.value) + ".length, "
                    elif str(type(stmt_Subscript.value))[13:-2] == "Name":
                        data += stmt_Subscript.value.id + ".length, "
                    else:
                        print debug_warning
                        print "type not supported yet => ", str(type(stmt_Subscript.value))
                        exit(1)
                else:
                    data += "0, "
            else:
                print debug_warning
                print "Type not recognized => ", type(stmt_Subscript.slice.lower)
                exit(1)
            if isinstance(stmt_Subscript.slice.upper, _ast.Num):
                data += str(stmt_Subscript.slice.upper.n) + ", "
            elif stmt_Subscript.slice.upper == None:
                if stmt_Subscript.slice.step.n > 0:
                    if str(type(stmt_Subscript.value))[13:-2] == "Subscript":
                        data += self.subscriptHandle(stmt_Subscript.value) + ".length, "
                    elif str(type(stmt_Subscript.value))[13:-2] == "Name":
                        data += stmt_Subscript.value.id + ".length, "
                    else:
                        print debug_warning
                        print "type not supported yet => ", str(type(stmt_Subscript.value))
                        exit(1)
                else:
                    data += "0, "
            else:
                print debug_warning
                print "Type not recognized => ", type(stmt_Subscript.slice.upper)
                exit(1)
            if isinstance(stmt_Subscript.slice.step, _ast.Num):
                data += str(stmt_Subscript.slice.step.n) + ")"
            elif stmt_Subscript.slice.step == None:
                data += "1)"
            else:
                print debug_warning
                print "Type not recognized => ", type(stmt_Subscript.slice.upper)
                exit(1)
        else:
            print debug_warning
            print "Type not recognized => ", type(stmt_Subscript.slice)
            exit(1)
        return data

    def visit_Print(self, stmt_print):
        global code

        self.addImport("dart:io")

        data = ""
        i = 0
        values = len(stmt_print.values)
        while (i < values):
            code += " stdout.write("

            if isinstance(stmt_print.values[i], _ast.Str):
                data = "'" + self.escape(stmt_print.values[i].s) + "'"
            elif isinstance(stmt_print.values[i], _ast.Num):
                data = stmt_print.values[i].n
            elif isinstance(stmt_print.values[i], _ast.Name):
                data = stmt_print.values[i].id
            elif isinstance(stmt_print.values[i], _ast.List):
                data = self.parseList(stmt_print.values[i].elts)
            elif isinstance(stmt_print.values[i], _ast.BinOp):
                data = self.parseExp(stmt_print.values[i])
            elif isinstance(stmt_print.values[i], _ast.Call):
                self.visit_Call(stmt_print.values[i], True)
            elif isinstance(stmt_print.values[i], _ast.Subscript):
                data = self.subscriptHandle(stmt_print.values[i])
            elif isinstance(stmt_print.values[i], _ast.Attribute):
                data = self.attrHandle(stmt_print.values[i])
            else:
                print debug_warning
                print "Type not recognized => ", str(type(stmt_print.values[i]))
                exit(1)

            code += str(data) + ");"
            if (i + 1) < values:
                code += " stdout.write(' ');"
            else:
                code += " stdout.write('\\n');";
            i += 1

    def visit_Assign(self, stmt_assign):
        global code, funVars, funMode

        for target in stmt_assign.targets:
            if isinstance(target, _ast.Attribute):
                code += self.attrHandle(target) + " = "
            else:
                if funMode:
                    if funVars.__contains__(target.id) == False:
                        funVars.append(target.id)
                        code += " var"
                else:
                    if symTab.__contains__(target.id) == False:
                        symTab.append(target.id)
                        code += " var"

                code += " " + target.id + " = ";

            value = ""
            if isinstance(stmt_assign.value, _ast.Num):
                value = stmt_assign.value.n
            elif isinstance(stmt_assign.value, _ast.Str):
                value = "'" + stmt_assign.value.s + "'"
            elif isinstance(stmt_assign.value, _ast.List):
                value = self.parseList(stmt_assign.value.elts)
            elif isinstance(stmt_assign.value, _ast.Name):
                value = stmt_assign.value.id
            elif isinstance(stmt_assign.value, _ast.BinOp):
                value = self.parseExp(stmt_assign.value)
            elif isinstance(stmt_assign.value, _ast.Call):
                self.visit_Call(stmt_assign.value, True)
            elif isinstance(stmt_assign.value, _ast.Subscript):
                value = self.subscriptHandle(stmt_assign.value)
            else:
                print debug_warning
                print "Type not recognized => ", type(stmt_assign.value)
                exit(1)
            if value != "":
                 code += str(value)
            code += ";"

    def visit_If(self, stmt_if):
        global code

        code += " if ("
        if hasattr(stmt_if.test, 'left'):
            varType = str(type(stmt_if.test.left))[13:-2]
            if varType == "Name":
                if stmt_if.test.left.id == 'True':
                    code += "true"
                elif stmt_if.test.left.id == 'False':
                    code += "false"
                else:
                    code += stmt_if.test.left.id
            elif varType == "Str":
                code += stmt_if.test.left.s
            elif varType == "Num":
                code += str(stmt_if.test.left.n)
            elif varType == "BinOp":
                code += self.parseExp(stmt_if.test.left)
            else:
                print debug_warning
                print "Type not recognized => ", varType
                exit(1)
        elif str(type(stmt_if.test))[13:-2] == "Name":
            if stmt_if.test.id == "True":
                code += "true"
            elif stmt_if.test.id == "False":
                code += "false"

        if hasattr(stmt_if.test, 'ops'):
            code += operators[str(type(stmt_if.test.ops[0]))[8:-2]]

        if hasattr(stmt_if.test, 'comparators'):
            varType = str(type(stmt_if.test.comparators[0]))[13:-2]
            if varType == "Name":
                if stmt_if.test.comparators[0].id == 'True':
                    code += "true"
                elif stmt_if.test.comparators[0].id == 'False':
                    code += "false"
                else:
                    code += stmt_if.test.comparators[0].id
            elif varType == "Str":
                code += stmt_if.test.comparators[0].s
            elif varType == "Num":
                code += str(stmt_if.test.comparators[0].n)
            elif varType == "BinOp":
                code += self.parseExp(stmt_if.test.comparators[0])
            else:
                print debug_warning
                print "Type not recognized => ", varType
                exit(1)

        code += ") {"
        for node in stmt_if.body:
            self.visit(node)

        code += " }"
        if len(stmt_if.orelse) > 0:
            code += " else {"
            for node in stmt_if.orelse:
                self.visit(node)
            code += " }"

    def visit_For(self, stmt_For):
        global code

        code += " for (var " + stmt_For.target.id + " in "

        if isinstance(stmt_For.iter, _ast.Call):
            self.visit_Call(stmt_For.iter, True)
        elif isinstance(stmt_For.iter, _ast.Name):
            code += stmt_For.iter.id
        else:
            print "This type of for loop not yet handled"
            exit(1)

        code += " ) {"

        for node in stmt_For.body:
            self.visit(node)

        code += "}"

        if len(stmt_For.orelse) > 0:
            for node in stmt_For.orelse:
                self.visit(node)

    def visit_While(self, stmt_while):
        global code

        code += " while ("
        varType = str(type(stmt_while.test.left))[13:-2]

        if varType == "Name":
            if stmt_while.test.left.id == 'True':
                code += "true"
            elif stmt_while.test.left.id == 'False':
                code += "false"
            else:
                code += stmt_while.test.left.id
        elif varType == "Str":
           code += stmt_while.test.left.s
        elif varType == "Num":
            code += str(stmt_while.test.left.n)
        else:
            print debug_warning
            print "Type not recognized => ", varType
            exit(1)

        code += operators[str(type(stmt_while.test.ops[0]))[8:-2]]
        varType = str(type(stmt_while.test.comparators[0]))[13:-2]

        if varType == "Name":
            if stmt_while.test.comparators[0].id == 'True':
                code += "true"
            elif stmt_while.test.comparators[0].id == 'False':
                code += "false"
            else:
                code += stmt_while.test.comparators[0].id
        elif varType == "Str":
            code += stmt_while.test.comparators[0].s
        elif varType == "Num":
            code += str(stmt_while.test.comparators[0].n)
        else:
            print debug_warning
            print "Type not recognized => ", varType
            exit(1)

        code += ") {"

        for node in stmt_while.body:
            self.visit(node)

        code += "}"

    def  visit_AugAssign(self, stmt_aug_assign):
        global code
        powFlag = False

        if isinstance(stmt_aug_assign.target, _ast.Attribute):
            code += self.attrHandle(stmt_aug_assign.target)
        else:
            code += " " + stmt_aug_assign.target.id

        op = str(type(stmt_aug_assign.op))[8:-2]
        if op in operators:
            code += operators[op] + "="
        elif isinstance(stmt_aug_assign.op, _ast.Pow):
            self.addImport('dart:math')
            code += " = pow ("
            code += stmt_aug_assign.target.id
            code += ", "
            powFlag = True
        else:
            print debug_warning
            print "Operator not implemented => " + op
            exit(1)

        if isinstance(stmt_aug_assign.value, _ast.Num):
            code += str(stmt_aug_assign.value.n)
        elif isinstance(stmt_aug_assign.value, _ast.Name):
            code += str(stmt_aug_assign.value.id)
        elif isinstance(stmt_aug_assign.value, _ast.BinOp):
            code += self.parseExp(stmt_aug_assign.value)
        elif isinstance(stmt_aug_assign.value, _ast.Attribute):
            code += self.attrHandle(stmt_aug_assign.value)

        if powFlag:
            code += ")"

        code += ";"

    def visit_FunctionDef(self, stmt_function):
        global code, funVars, funMode

        temp = code
        code = ""
        funMode = True

        if stmt_function.name == "__init__":
            code = " " + classes[-1] + "("
        else:
            code = " " + stmt_function.name + "("

        i = 0
        alen = len(stmt_function.args.args)
        while i < alen:
            if str(stmt_function.args.args[i].id) == "self":
                i += 1
                continue

            code += stmt_function.args.args[i].id
            funVars.append(stmt_function.args.args[i].id)

            if (i + 1) < alen:
                code += ", "
            i += 1
        code += ") {"

        for node in stmt_function.body:
            self.visit(node)

        funMode = False
        code += " }"
        funVars = []

        code = code + temp

    def visit_Call(self, stmt_call, myVar = False):
        global code, expCall, func, classes, inbuilts

        if isinstance(stmt_call.func, _ast.Attribute):
            if expCall:
                func += self.attrHandle(stmt_call)
            else:
                code += self.attrHandle(stmt_call)

            if myVar == False:
                if expCall:
                    func += ";"
                else:
                    code += ";"
            return

        if stmt_call.func.id in inbuilts:
            self.addImport("lib/inbuilts.dart")

        if classes.__contains__(stmt_call.func.id):
            if expCall:
                func += "new "
            else:
                code += "new "

        if expCall:
            func += stmt_call.func.id + "("
        else:
            code += stmt_call.func.id + "("

        alen = len(stmt_call.args)
        i = 0
        p = ""

        while i < alen:
            if isinstance(stmt_call.args[i], _ast.Name):
                p = stmt_call.args[i].id
            elif isinstance(stmt_call.args[i], _ast.Num):
                p = stmt_call.args[i].n
            elif isinstance(stmt_call.args[i], _ast.Str):
                p = "'" + stmt_call.args[i].s + "'"
            elif isinstance(stmt_call.args[i], _ast.List):
                p = self.parseList(stmt_call.args[i].elts)
            elif isinstance(stmt_call.args[i], _ast.BinOp):
                p = self.parseExp(stmt_call.args[i])
            elif isinstance(stmt_call.args[i], _ast.Call):
                p = self.visit_Call(stmt_call.args[i], True)
            elif isinstance(stmt_call.args[i], _ast.Attribute):
                p = self.attrHandle(stmt_call.args[i])
            else:
                print debug_warning
                print "Type not recognized => ", stmt_call.args[i]
                exit(1)

            if p is not None:
                if expCall:
                    func += str(p)
                else:
                    code += str(p)

            if (i + 1) < alen:
                if expCall:
                    func += ", "
                else:
                    code += ", "
            i += 1

        if expCall:
            func += ")"
        else:
            code += ")"

        if myVar == False:
            code += ";"

    def visit_Return(self, stmt_return):
        global code

        code += " return "
        v = ""

        if isinstance(stmt_return.value, _ast.Name):
            if stmt_return.value.id == "self":
                v = "this"
            else:
                v = stmt_return.value.id
        elif isinstance(stmt_return.value, _ast.Num):
            v = stmt_return.value.n
        elif isinstance(stmt_return.value, _ast.Str):
            v = "'" + stmt_return.value.s + "'"
        elif isinstance(stmt_return.value, _ast.List):
            v = self.parseList(stmt_return.value.elts)
        elif isinstance(stmt_return.value, _ast.BinOp):
            v = self.parseExp(stmt_return.value)
        elif isinstance(stmt_return.value, _ast.Call):
            self.visit_Call(stmt_return.value, True)

        if v != "":
            code += str(v)
        code += ";"

    def visit_ClassDef(self, stmt_class):
        global code, funMode

        main = code
        code = ""
        funMode = True

        code = " class " + stmt_class.name
        if classes.__contains__(stmt_class.name) == False:
            classes.append(stmt_class.name)

        if len(stmt_class.bases) == 1:
            code += " extends " + str(stmt_class.bases[0].id)
        elif len(stmt_class.bases) > 1:
            print "Multiple Inheritace is unsupported at the moment :( Sorry!"
            exit(1)
        code += " {"

        temp = code
        code = ""

        for node in stmt_class.body:
            self.visit(node)

        code = temp + code + " }" + main
        funMode = False
        funVars = []

MyParser().parse(open(sys.argv[1]).read())

code += " }"

for imp in imports:
    code = "import '" + imp + "'; " + code

outFile.write(code)
outFile.close()