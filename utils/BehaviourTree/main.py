from rich import print

from npc.npc import Cow, NPC


def main() -> None:
    DURATION = 50.0
    loop_count = 0.0
    # npc = Cow()
    npc = NPC()
    npc.init_ai()

    while loop_count < DURATION:
        loop_count += 1.0
        print(f"[cyan]loop[/] {loop_count:4.1f} [cyan]###########################################################")
        # ai.update(0.0)
        npc.ai.move(loop_count)


if __name__ == "__main__":
    main()
