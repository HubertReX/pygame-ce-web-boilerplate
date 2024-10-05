import sys
sys.path.append("project")
try:
    from project.main import main
except ImportError as e:
    print(e)
    with open("debug.log", "w") as f:
        f.write(repr(e))

if __name__ == "__main__":
    print("test")
    # main()
