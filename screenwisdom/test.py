from dataclasses import dataclass


@dataclass
class MyClass:
    name: str
    age: int

    def __init__(self, name: str, age: int, additional_info: str):
        self.additional_info = additional_info
        super().__init__(name, age)  # Call the parent class constructor


# Example usage
obj = MyClass(name="Alice", age=30, additional_info="Some additional information")
print(obj)  # Output: MyClass(name='Alice', age=30)
print(obj.additional_info)  # Output: Some additional information
