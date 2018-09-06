from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, List

from monkey import ast

INTEGER_OBJ = 'INTEGER'
BOOLEAN_OBJ = 'BOOLEAN'
NULL_OBJ = 'NULL'
RETURN_VALUE_OBJ = 'RETURN_VALUE'
ERROR_OBJ = 'ERROR'
FUNCTION_OBJ = 'FUNCTION'


@dataclass
class ObjectType:
    TypeName: str


class Object:
    Value: Any

    @property
    @abstractmethod
    def Type(self) -> ObjectType:
        pass

    @property
    @abstractmethod
    def Inspect(self) -> str:
        pass


@dataclass
class AnyObject(Object):
    Value: Object

    @property
    def Type(self) -> ObjectType:
        return self.Value.Type

    @property
    def Inspect(self) -> str:
        return self.Value.Inspect


@dataclass
class Integer(Object):
    Value: int

    @property
    def Type(self) -> ObjectType:
        return ObjectType(INTEGER_OBJ)

    @property
    def Inspect(self) -> str:
        return str(self.Value)


@dataclass
class Boolean(Object):
    Value: bool

    @property
    def Type(self) -> ObjectType:
        return ObjectType(BOOLEAN_OBJ)

    @property
    def Inspect(self) -> str:
        return str(self.Value)


@dataclass
class Null(Object):
    @property
    def Type(self) -> ObjectType:
        return ObjectType(NULL_OBJ)

    @property
    def Inspect(self) -> str:
        return NULL_OBJ


@dataclass
class ReturnValue(Object):
    Value: Object

    @property
    def Type(self) -> ObjectType:
        return ObjectType(RETURN_VALUE_OBJ)

    @property
    def Inspect(self) -> str:
        return self.Value.Inspect


@dataclass
class Error(Object):
    Message: str

    @property
    def Type(self) -> ObjectType:
        return ObjectType(ERROR_OBJ)

    @property
    def Inspect(self) -> str:
        return 'ERROR: ' + self.Message


@dataclass
class Function(Object):
    Parameters: List[ast.Identifier]
    Body: ast.BlockStatement
    Env: Any

    @property
    def Type(self) -> ObjectType:
        return ObjectType(FUNCTION_OBJ)

    @property
    def Inspect(self) -> str:
        out: List[str] = []

        params: List[str] = []
        for p in self.Parameters:
            params.append(p.String())

        out.append('fn')
        out.append('(')
        out.append(', '.join(params))
        out.append(') {\n')
        out.append(self.Body.String())
        out.append('\n}')

        return ''.join(out)
