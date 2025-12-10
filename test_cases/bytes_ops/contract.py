from algopy import Bytes, Contract, arc4, UInt64, subroutine, op

class BiguintBinaryOps(Contract):
    def approval_program(self) -> bool:
        do_some_ops(
            left=Bytes.from_hex("FF"),
            right=Bytes.from_hex("0F"),
            concat=Bytes.from_hex("FF0F"),
            bitwise_or=Bytes.from_hex("FF"),
            bitwise_xor=Bytes.from_hex("F0"),
            bitwise_and=Bytes.from_hex("0F"),
        )
        do_augmented_assignment_ops(Bytes.from_hex("FF"))
        do_byteops_with_structs(Point(UInt64(1), UInt64(2)),
                                Point(UInt64(3), UInt64(4)))
        return True

    def clear_state_program(self) -> bool:
        return True


@subroutine
def do_some_ops(
    *,
    left: Bytes,
    right: Bytes,
    concat: Bytes,
    bitwise_or: Bytes,
    bitwise_xor: Bytes,
    bitwise_and: Bytes,
) -> None:
    result = left + right
    assert result == concat
    result = left | right
    assert result == bitwise_or
    result = left ^ right
    assert result == bitwise_xor
    result = left & right
    assert result == bitwise_and


@subroutine
def do_augmented_assignment_ops(seed: Bytes) -> None:
    seed &= Bytes.from_hex("00")

    assert seed == Bytes.from_hex("00")

    five = Bytes.from_hex("05")

    seed |= five

    assert seed == five

    sixteen = Bytes.from_hex("10")

    seed ^= sixteen

    assert seed == Bytes.from_hex("15")

    seed ^= five

    assert seed == sixteen

    seed += five

    assert seed == Bytes.from_hex("1005")

class Point(arc4.Struct):
    x: UInt64
    y: UInt64

@subroutine()
def do_byteops_with_structs(a: Point, b: Point) -> None:
        assert op.concat(a, b) == (a.bytes + b.bytes)
