def greet(name):
    return f"Hello, {name}! Claude Code is working."

def add(a, b):
    return a + b

if __name__ == "__main__":
    print(greet("Dan"))
    print(f"2 + 3 = {add(2, 3)}")

    # Quick assertion test
    assert add(2, 3) == 5
    assert greet("Test") == "Hello, Test! Claude Code is working."
    print("All tests passed.")
