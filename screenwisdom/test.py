from dataclasses import dataclass, field


@dataclass
class A:
    def __post_init__(self):
        print("A")

@dataclass
class B(A):
    def __post_init__(self):
        super().__post_init__()
        print("B")

B()
