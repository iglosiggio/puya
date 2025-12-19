import typing
from collections.abc import Sequence

from puya import log
from puya.awst import wtypes
from puya.awst.nodes import (
    BinaryBooleanOperator,
    BoolConstant,
    BooleanBinaryOperation,
    Expression,
    Not,
    NumericComparison,
    NumericComparisonExpression,
    ReinterpretCast,
)
from puya.parse import SourceLocation
from puyapy import models
from puyapy.awst_build import intrinsic_factory, pytypes
from puyapy.awst_build.eb import _expect as expect
from puyapy.awst_build.eb._base import NotIterableInstanceExpressionBuilder
from puyapy.awst_build.eb.interface import (
    BuilderBinaryOp,
    BuilderComparisonOp,
    InstanceBuilder,
    LiteralBuilder,
    NodeBuilder,
    TypeBuilder,
)

logger = log.get_logger(__name__)


class BoolTypeBuilder(TypeBuilder):
    def __init__(self, location: SourceLocation):
        super().__init__(pytypes.BoolType, location)

    @typing.override
    def try_convert_literal(
        self, literal: LiteralBuilder, location: SourceLocation
    ) -> InstanceBuilder | None:
        match literal.value:
            case bool(literal_value):
                expr = BoolConstant(value=literal_value, source_location=location)
                return BoolExpressionBuilder(expr)
        return None

    @typing.override
    def call(
        self,
        args: Sequence[NodeBuilder],
        arg_kinds: list[models.ArgKind],
        arg_names: list[str | None],
        location: SourceLocation,
    ) -> InstanceBuilder:
        arg = expect.at_most_one_arg(args, location)
        match arg:
            case None:
                false = BoolConstant(value=False, source_location=location)
                return BoolExpressionBuilder(false)
            case InstanceBuilder(pytype=pytypes.BoolType):
                return arg
            case _:
                return arg.bool_eval(location)


class BoolExpressionBuilder(NotIterableInstanceExpressionBuilder):
    def __init__(self, expr: Expression):
        super().__init__(pytypes.BoolType, expr)

    @typing.override
    def to_bytes(self, location: SourceLocation) -> Expression:
        return intrinsic_factory.itob(self.resolve(), location)

    @typing.override
    def bool_eval(self, location: SourceLocation, *, negate: bool = False) -> InstanceBuilder:
        if not negate:
            return self
        return BoolExpressionBuilder(Not(location, self.resolve()))

    @typing.override
    def compare(
        self, other: InstanceBuilder, op: BuilderComparisonOp, location: SourceLocation
    ) -> InstanceBuilder:
        if other.pytype != pytypes.BoolType:
            return NotImplemented  # type: ignore[no-any-return]
        cmp_expr = NumericComparisonExpression(
            source_location=location,
            lhs=self.resolve(),
            operator=NumericComparison(op.value),
            rhs=other.resolve(),
        )
        return BoolExpressionBuilder(cmp_expr)

    @typing.override
    def bool_binary_op(
        self, other: InstanceBuilder, op: BinaryBooleanOperator, location: SourceLocation
    ) -> InstanceBuilder:
        if other.pytype != pytypes.BoolType:
            return super().bool_binary_op(other, op, location)
        result = BooleanBinaryOperation(
            left=self.resolve(),
            op=op,
            right=other.resolve(),
            source_location=location,
        )
        return BoolExpressionBuilder(result)

    def binary_op(
        self,
        other: InstanceBuilder,
        op: BuilderBinaryOp,
        location: SourceLocation,
        *,
        reverse: bool,
    ) -> InstanceBuilder:
        # If we try to import it at the top level we end up with cyclic imports
        from puyapy.awst_build.eb.uint64 import UInt64ExpressionBuilder

        # Booleans behave like UInt64 under arithmetic operations.
        # Let's cast ourselves to UInt64 and use the logic there.
        cast = ReinterpretCast(
            expr=self.resolve(),
            wtype=wtypes.uint64_wtype,
            source_location=self.source_location,
        )
        return UInt64ExpressionBuilder(cast).binary_op(other, op, location, reverse=reverse)
