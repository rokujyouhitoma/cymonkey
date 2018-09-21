import unittest
from dataclasses import dataclass
from typing import Callable, List

from monkey import ast, token


class TestAst(unittest.TestCase):
    def test_string(self):
        program = ast.Program(Statements=[
            ast.LetStatement(
                Token=token.Token(Type=token.LET, Literal='let'),
                Name=ast.Identifier(
                    Token=token.Token(Type=token.IDENT, Literal='myVar'), Value='myVar'),
                Value=ast.Identifier(
                    Token=token.Token(Type=token.IDENT, Literal='anotherVar'), Value='anotherVar'))
        ])

        if program.String() != 'let myVar = anotherVar;':
            self.fail('program.String() wrong. got=\'%s\'' % program.String())

    def test_modify(self):
        one: Callable[[], ast.Expression] = lambda: ast.IntegerLiteral(
            Token=token.Token(token.INT, 'Unknown'), Value=1)
        two: Callable[[], ast.Expression] = lambda: ast.IntegerLiteral(
            Token=token.Token(token.INT, 'Unknown'), Value=2)

        def turnOneIntoTwo(node: ast.Node) -> ast.Node:
            integer = node
            if type(node) != ast.IntegerLiteral:
                return node

            if integer.Value != 1:
                return node

            integer.Value = 2
            return integer

        @dataclass
        class Test:
            input: ast.Node
            expected: ast.Node

        tests: List[Test] = [
            Test(one(), two()),
            Test(
                ast.Program(Statements=[
                    ast.ExpressionStatement(
                        Token=token.Token(token.INT, 'Unknown'), ExpressionValue=one()),
                ]),
                ast.Program(Statements=[
                    ast.ExpressionStatement(
                        Token=token.Token(token.INT, 'Unknown'), ExpressionValue=two()),
                ])),
        ]

        for tt in tests:
            modified = ast.Modify(tt.input, turnOneIntoTwo)

            if modified != tt.expected:
                self.fail('not equal. got=%s, want=%s' % (modified, tt.expected))
