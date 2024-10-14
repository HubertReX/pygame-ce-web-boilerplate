from rich import print

from NPC_behavior_tree import PatrolBehaviorTree


def main() -> None:
    ai = PatrolBehaviorTree()

    DURATION = 20.0
    loop_count = 0.0

    while loop_count < DURATION:
        loop_count += 1.0
        print(f"[cyan]loop[/] {loop_count:4.1f} [cyan]###########################################################")
        ai.update(1.0)


if __name__ == "__main__":
    main()
