from typing import List, Optional
from node import Node


class Jarra(Node):
    def getState(self, index: int) -> Optional[List[int]]:
        """
        Returns the next state of the jars after applying the operator at the given index.
        List of operators:
        0: Fill the first jar with 3 liters of water.
        1: Fill the second jar with 4 liters of water.
        2: Empty the first jar.
        3: Empty the second jar.
        4: Pour the water from the first jar into the second jar.
        5: Pour the water from the second jar into the first jar.
        """
        state: List[int] = self.state # The Jars, [3L, 4L]
        nextState: Optional[List[int]] = None

        if index == 0:
            """
            The first jar is filled with 3 liters of water.
            """
            if state[0] < 3:
                """
                If the first jar is not full, fill it.
                """
                nextState = [3, state[1]]
            else:
                """
                If the first jar is full, do nothing.
                """
                nextState = None
        elif index == 1:
            """
            The second jar is filled with 4 liters of water.
            """
            if state[1] < 4:
                """
                If the second jar is not full, fill it.
                """
                nextState = [state[0], 4]
            else:
                """
                If the second jar is full, do nothing.
                """
                nextState = None
        elif index == 2:
            """
            The first jar is emptied.
            """
            if state[0] > 0:
                """
                If the first jar is not empty, empty it.
                """
                nextState = [0, state[1]]
            else:
                """
                If the first jar is empty, do nothing.
                """
                nextState = None
        elif index == 3:
            """
            The second jar is emptied.
            """
            if state[1] > 0:
                """
                If the second jar is not empty, empty it.
                """
                nextState = [state[0], 0]
            else:
                """
                If the second jar is empty, do nothing.
                """
                nextState = None
        elif index == 4:
            """
            The water from the first jar is poured into the second jar.
            """
            nextState = self.trasvasar3L4L(state)
        elif index == 5:
            """
            The water from the second jar is poured into the first jar.
            """
            nextState = self.trasvasar4L3L(state)

        return nextState if state != nextState else None

    def trasvasar4L3L(self, state: List[int]) -> List[int]:
        t: int = min(3 - state[0], state[1])
        return [state[0] + t, state[1] - t]

    def trasvasar3L4L(self, state: List[int]) -> List[int]:
        t: int = min(state[0], 4 - state[1])
        return [state[0] - t, state[1] + t]

    def cost(self) -> int:
        return self.level
