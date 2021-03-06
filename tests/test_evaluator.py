import unittest
from dataclasses import dataclass
from typing import Any, List

from monkey import ast, evaluator, lexer, object, parser


class TestEvaluator(unittest.TestCase):
    def test_eval_integer_expression(self):
        @dataclass
        class Test():
            input: str
            expected: int

        tests: List[Test] = [
            Test('5', 5),
            Test('10', 10),
            Test('-5', -5),
            Test('-10', -10),
            Test('5 + 5 + 5 + 5 - 10', 10),
            Test('2 * 2 * 2 * 2 * 2', 32),
            Test('-50 + 100 + -50', 0),
            Test('5 * 2 + 10', 20),
            Test('5 + 2 * 10', 25),
            Test('20 + 2 * -10', 0),
            Test('50 / 2 * 2 + 10', 60),
            Test('2 * (5 + 10)', 30),
            Test('3 * 3 * 3 + 10', 37),
            Test('3 * (3 * 3) + 10', 37),
            Test('(5 + 10 * 2 + 15 / 3) * 2 + -10', 50),
        ]

        for tt in tests:
            evaluated = testEval(tt.input)
            testIntegerObject(self, evaluated, tt.expected)

    def test_eval_boolean_expression(self):
        @dataclass
        class Test():
            input: str
            expected: bool

        tests: List[Test] = [
            Test('true', True),
            Test('false', False),
            Test('1 < 2', True),
            Test('1 > 2', False),
            Test('1 < 1', False),
            Test('1 > 1', False),
            Test('1 == 1', True),
            Test('1 != 1', False),
            Test('1 == 2', False),
            Test('1 != 2', True),
            Test('true == true', True),
            Test('false == false', True),
            Test('true == false', False),
            Test('true != false', True),
            Test('false != true', True),
            Test('(1 < 2) == true', True),
            Test('(1 < 2) == false', False),
            Test('(1 > 2) == true', False),
            Test('(1 > 2) == false', True),
        ]

        for tt in tests:
            evaluated = testEval(tt.input)
            testBooleanObject(self, evaluated, tt.expected)

    def test_bang_operator(self):
        @dataclass
        class Test():
            input: str
            expected: bool

        tests: List[Test] = [
            Test('!true', False),
            Test('!false', True),
            Test('!5', False),
            Test('!!true', True),
            Test('!!false', False),
            Test('!!5', True),
        ]

        for tt in tests:
            evaluated = testEval(tt.input)
            testBooleanObject(self, evaluated, tt.expected)

    def test_if_else_expressions(self):
        @dataclass
        class Test():
            input: str
            expected: Any

        tests: List[Test] = [
            Test('if (true) { 10 }', 10),
            Test('if (false) { 10 }', None),
            Test('if (1) { 10 }', 10),
            Test('if (1 < 2) { 10 }', 10),
            Test('if (1 > 2) { 10 }', None),
            Test('if (1 > 2) { 10 } else { 20 }', 20),
            Test('if (1 < 2) { 10 } else { 20 }', 10),
        ]

        for tt in tests:
            evaluated = testEval(tt.input)
            integer = tt.expected
            if integer:
                testIntegerObject(self, evaluated, int(integer))
            else:
                testNullObject(self, evaluated)

    def test_return_statements(self):
        @dataclass
        class Test():
            input: str
            expected: int

        tests: List[Test] = [
            Test('return 10;', 10),
            Test('return 10; 9;', 10),
            Test('return 2 * 5; 9;', 10),
            Test('9; return 2 * 5; 9;', 10),
            Test(
                '''
            if (10 > 1) {
              if (10 > 1) {
                return 10;
              }
              return 1;
            }
            ''', 10),
        ]

        for tt in tests:
            evaluated = testEval(tt.input)
            testIntegerObject(self, evaluated, tt.expected)

    def test_error_handling(self):
        @dataclass
        class Test():
            input: str
            expectedMessage: str

        tests: List[Test] = [
            Test('5 + true;', 'type mismatch: INTEGER + BOOLEAN'),
            Test('5 + true; 5;', 'type mismatch: INTEGER + BOOLEAN'),
            Test('-true', 'unknown operator: -BOOLEAN'),
            Test('true + false;', 'unknown operator: BOOLEAN + BOOLEAN'),
            Test('5; true + false; 5', 'unknown operator: BOOLEAN + BOOLEAN'),
            Test('if (10 > 1) { true + false; }', 'unknown operator: BOOLEAN + BOOLEAN'),
            Test(
                '''
            if (10 > 1) {
              if (10 > 1) {
                return true + false;
              }
              return 1;
            }
            ''', 'unknown operator: BOOLEAN + BOOLEAN'),
            Test('foobar', 'identifier not found: foobar'),
            Test('"Hello" - "World"', 'unknown operator: STRING - STRING'),
            Test('{"name": "Monkey"}[fn(x) { x }];', 'unusable as hash key: FUNCTION'),
        ]

        for tt in tests:
            evaluated = testEval(tt.input)
            errObj = evaluated
            if errObj == evaluator.NULL:
                self.fail('no error object returned. got=%s(%s)' % (evaluated, evaluated))
                continue

            if errObj.Message != tt.expectedMessage:
                print(errObj.Message)
                self.fail('wrong error message. expected=%s, got=%s' % (tt.expectedMessage,
                                                                        errObj.Message))

    def test_let_statements(self):
        @dataclass
        class Test:
            input: str
            expected: int

        tests: List[Test] = [
            Test('let a = 5; a;', 5),
            Test('let a = 5 * 5; a;', 25),
            Test('let a = 5; let b = a; b;', 5),
            Test('let a = 5; let b = a; let c = a + b + 5; c;', 15),
        ]

        for tt in tests:
            testIntegerObject(self, testEval(tt.input), tt.expected)

    def test_function_object(self):
        input = 'fn(x) { x + 2; };'
        evaluated = testEval(input)

        fn = evaluated
        if not fn:
            self.fail('object is not Function. got=%s (%s)' % (evaluated, evaluated))

        if len(fn.Parameters) != 1:
            self.fail('function has wrong parameters. Parameters=%s' % fn.Parameters)

        if fn.Parameters[0].String() != 'x':
            self.fail('parameter is not \'x\'. got=%s' % fn.Parameters[0])

        expectedBody = '(x + 2)'

        if fn.Body.String() != expectedBody:
            self.fail('body is not %s. got=%s' % (expectedBody, fn.Body.String()))

    def test_function_application(self):
        @dataclass
        class Test:
            input: str
            expected: int

        tests: List[Test] = [
            Test('let identity = fn(x) { x; }; identity(5);', 5),
            Test('let identity = fn(x) { return x; }; identity(5);', 5),
            Test('let double = fn(x) { x * 2; }; double(5);', 10),
            Test('let add = fn(x, y) { x + y; }; add(5, 5);', 10),
            Test('let add = fn(x, y) { x + y; }; add(5 + 5, add(5, 5));', 20),
            Test('fn(x) { x; }(5)', 5),
        ]

        for tt in tests:
            testIntegerObject(self, testEval(tt.input), tt.expected)

    def test_closures(self):
        input = '''
        let newAdder = fn(x) {
          fn(y) { x + y };
        };

        let addTwo = newAdder(2);
        addTwo(2);'''
        testIntegerObject(self, testEval(input), 4)

    def test_string_literal(self):
        input = '"Hello World!"'
        evaluated = testEval(input)
        if not evaluated:
            self.fail('object is not String. got=%s (%s)' % (evaluated, evaluated))
        if evaluated.Value != 'Hello World!':
            self.fail('String has wrong value. got=%s' % str.Value)

    def test_builtin_functions(self):
        @dataclass
        class Test:
            input: str
            expected: Any

        tests = [
            Test('len("")', 0),
            Test('len("four")', 4),
            Test('len("hello world")', 11),
            Test('len(1)', 'argument to \'len\' not supported, got INTEGER'),
            Test('len("one", "two")', 'wrong number of arguments. got=2, want=1'),
        ]

        for tt in tests:
            evaluated = testEval(tt.input)
            expected = tt.expected
            if type(expected) == int:
                testIntegerObject(self, evaluated, expected)
            elif type(expected) == str:
                errObj = evaluated
                if not errObj:
                    self.fail('object is not Error. got=%s (%s)' % (evaluated, evaluated))
                    continue
                if errObj.Message != expected:
                    self.fail(
                        'wrong error message. expected=%s, got=%s' % (expected, errObj.Message))

    def test_array_literals(self):
        input = '[1, 2 * 2, 3 + 3]'

        evaluated = testEval(input)
        result = evaluated
        if not result:
            self.fail('object is not Array. got=%s (%s)' % (evaluated, evaluated))

        if len(result.Elements) != 3:
            self.fail('array has wrong num of elements. got=%s' % len(result.Elements))

        testIntegerObject(self, result.Elements[0], 1)
        testIntegerObject(self, result.Elements[1], 4)
        testIntegerObject(self, result.Elements[2], 6)

    def test_array_index_expressions(self):
        @dataclass
        class Test:
            input: str
            expected: Any

        tests: List[Test] = [
            Test('[1, 2, 3][0]', 1),
            Test('[1, 2, 3][1]', 2),
            Test('[1, 2, 3][2]', 3),
            Test('let i = 0; [1][i];', 1),
            Test('[1, 2, 3][1 + 1];', 3),
            Test('let myArray = [1, 2, 3]; myArray[2];', 3),
            Test('let myArray = [1, 2, 3]; myArray[0] + myArray[1] + myArray[2];', 6),
            Test('let myArray = [1, 2, 3]; let i = myArray[0]; myArray[i]', 2),
            Test('[1, 2, 3][3]', None),
            Test('[1, 2, 3][-1]', None),
        ]

        for tt in tests:
            evaluated = testEval(tt.input)
            integer = tt.expected
            if integer:
                testIntegerObject(self, evaluated, int(integer))
            else:
                testNullObject(self, evaluated)

    def test_empty(self):
        input = ''

        evaluated = testEval(input)
        if evaluated:
            self.fail('evaluated is not empty')

    def test_hash_literals(self):
        input = '''let two = "two";
        {
          "one": 10 - 9,
          two: 1 + 1,
          "thr" + "ee": 6 / 2,
          4: 4,
          true: 5,
          false: 6
        }'''

        evaluated = testEval(input)
        result = evaluated
        if not result:
            self.fail('Eval didn\'t return Hash. got=%s (%s)' % (evaluated, evaluated))

        expected = [
            (object.GetHashKey(object.String(Value='one')), 1),
            (object.GetHashKey(object.String(Value='two')), 2),
            (object.GetHashKey(object.String(Value='three')), 3),
            (object.GetHashKey(object.Integer(Value=4)), 4),
            (object.GetHashKey(evaluator.TRUE), 5),
            (object.GetHashKey(evaluator.FALSE), 6),
        ]

        if len(result.Pairs) != len(expected):
            self.fail('Hash has wrong num of pairs. got=%s' % len(result.Pairs))

        for expectedKey, expectedValue in expected:
            # TODO: xxx
            pair = [x for x in result.Pairs if x[0].Value == expectedKey.Value][0][1]
            if not pair:
                self.fail('no pair for given key in Pairs')

            testIntegerObject(self, pair.Value, expectedValue)

    def test_hash_index_expressions(self):
        @dataclass
        class Test:
            input: str
            expected: Any

        tests: List[Test] = [
            Test('{"foo": 5}["foo"]', 5),
            Test('{"foo": 5}["bar"]', None),
            Test('let key = "foo"; {"foo": 5}[key]', 5),
            Test('{}["foo"]', None),
            Test('{5: 5}[5]', 5),
            Test('{true: 5}[true]', 5),
            Test('{false: 5}[false]', 5),
        ]

        for tt in tests:
            evaluated = testEval(tt.input)
            integer = tt.expected
            if integer:
                testIntegerObject(self, evaluated, int(integer))
            else:
                testNullObject(self, evaluated)


class TestMacro(unittest.TestCase):
    def test_quote(self):
        @dataclass
        class Test():
            input: str
            expected: str

        tests: List[Test] = [
            Test('quote(5)', '5'),
            Test('quote(5 + 8)', '(5 + 8)'),
            Test('quote(foobar)', 'foobar'),
            Test('quote(foobar + barfoo)', '(foobar + barfoo)'),
        ]

        for tt in tests:
            evaluated = testEval(tt.input)
            quote = evaluated
            if not quote:
                self.fail('expected *object.Quote. got=%s (%s)' % (evaluated, evaluated))

            if quote.Node is None:
                self.fail('quote.Node is nil')

            if quote.Node.String() != tt.expected:
                self.fail('not equal. got=%s, want=%s' % (quote.Node.String(), tt.expected))

    def test_quote_unquote(self):
        @dataclass
        class Test():
            input: str
            expected: str

        tests: List[Test] = [
            Test('quote(unquote(4))', '4'),
            Test('quote(unquote(4 + 4))', '8'),
            Test('quote(8 + unquote(4 + 4))', '(8 + 8)'),
            Test('quote(unquote(4 + 4) + 8)', '(8 + 8)'),
            Test('''let foobar = 8;
            quote(foobar)''', 'foobar'),
            Test('''let foobar = 8;
            quote(unquote(foobar))''', '8'),
            Test('quote(unquote(true))', 'true'),
            Test('quote(unquote(false))', 'false'),
            Test('quote(unquote(quote(4 + 4)))', '(4 + 4)'),
            Test(
                '''let quotedInfixExpression = quote(4 + 4);
            quote(unquote(4 + 4) + unquote(quotedInfixExpression))''', '(8 + (4 + 4))'),
        ]

        for tt in tests:
            evaluated = testEval(tt.input)
            quote = evaluated
            if not quote:
                self.fail('expected *object.Quote. got=%s (%s)' % (evaluated, evaluated))

            if quote.Node is None:
                self.fail('quote.Node is nil')

            if quote.Node.String() != tt.expected:
                self.fail('not equal. got=%s, want=%s' % (quote.Node.String(), tt.expected))


class TestDefineMacros(unittest.TestCase):
    def test_define_macros(self):
        input = '''
        let number = 1;
        let function = fn(x, y) { x + y };
        let mymacro = macro(x, y) { x + y; };
        '''

        env = object.NewEnvironment()
        program = testParseProgram(input)

        evaluator.DefineMacros(program, env)

        if len(program.Statements) != 2:
            print(program.String())
            self.fail('Wrong number of statements. got=%s' % len(program.Statements))

        ok = env.Get('number')
        if ok:
            self.fail('number should not be defined')

        ok = env.Get("function")
        if ok:
            self.fail('function should not be defined')

        obj = env.Get("mymacro")
        if not obj:
            self.fail('macro not in environment.')

        macro = obj
        if not macro:
            self.fail('object is not Macro. got=%s (%s)' % (obj, obj))

        if len(macro.Parameters) != 2:
            self.fail('Wrong number of macro parameters. got=%s' % len(macro.Parameters))

        if macro.Parameters[0].String() != 'x':
            self.fail('parameter is not \'x\'. got=%s' % macro.Parameters[0])

        if macro.Parameters[1].String() != 'y':
            self.fail('parameter is not \'y\'. got=%s' % macro.Parameters[1])

        expectedBody = '(x + y)'

        if macro.Body.String() != expectedBody:
            self.fail('body is not %s. got=%s' % (expectedBody, macro.Body.String()))


class TestExpandMacros(unittest.TestCase):
    def test_expand_macros(self):
        @dataclass
        class Test:
            input: str
            expected: str

        tests: List[Test] = [
            Test(
                '''let infixExpression = macro() { quote(1 + 2); };
            infixExpression();''', '(1 + 2)'),
            Test(
                '''let reverse = macro(a, b) { quote(unquote(b) - unquote(a)); };
            reverse(2 + 2, 10 - 5);''', '(10 - 5) - (2 + 2)'),
            Test(
                '''
            let unless = macro(condition, consequence, alternative) {
              quote(if (!(unquote(condition))) {
                unquote(consequence);
              } else {
                unquote(alternative);
              });
            };
            unless(10 > 5, puts("not greater"), puts("greater"));
            ''', 'if (!(10 > 5)) { puts("not greater") } else { puts("greater") }'),
        ]

        for tt in tests:
            expected = testParseProgram(tt.expected)
            program = testParseProgram(tt.input)

            env = object.NewEnvironment()
            evaluator.DefineMacros(program, env)
            expanded = evaluator.ExpandMacros(program, env)

            if expanded.String() != expected.String():
                self.fail('not equal. want=%s, got=%s' % (expected.String(), expanded.String()))


def testParseProgram(input: str) -> ast.Program:
    lex = lexer.New(input)
    p = parser.New(lex)
    return p.ParseProgram()


def testNullObject(self, obj: object.Object) -> bool:
    if obj != evaluator.NULL:
        self.fail('object is not NULL. got=%s (%s)' % (obj, obj))
        return False
    return True


def testEval(input: str) -> object.Object:
    lex = lexer.New(input)
    p = parser.New(lex)
    program = p.ParseProgram()
    env = object.NewEnvironment()
    return evaluator.Eval(program, env)


def testIntegerObject(self, obj: object.Object, expected: int) -> bool:
    result = obj
    if not result:
        self.fail('object is not Integer. got=%s (%s)' % (obj, obj))
        return False

    if result.Value != expected:
        self.fail('object has wrong value. got=%s, want=%s' % (result.Value, expected))
        return False

    return True


def testBooleanObject(self, obj: object.Object, expected: bool) -> bool:
    result = obj
    if not result:
        self.fail('object is not Boolean. got=%s (%s)' % (obj, obj))
        return False

    if result.Value != expected:
        self.fail('object has wrong value. got=%s, want=%s' % (result.Value, expected))
        return False

    return True
