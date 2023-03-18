def import_or_install(packagename: str):
    try:
        return __import__(packagename)
    except ImportError:
        rc = subprocess.check_call([sys.executable, "-m", "pip", "install", packagename])
        if rc != 0:
            raise RuntimeError(f"Could not install required package '{packagename}'!")
        return __import__(packagename)

pygame_import = import_or_install("pygame")
if pygame_import is not None:
    import pygame

import enum
import collections
import random

# Settings
SCRIPT_TITLE = "Maze test"
SCREEN_SIZE: tuple[int, int] = (1280, 720)
BLOCK_SIZE: int = 24
FONT_SIZE: int = 20
FPS: int = 60
COL_BACKGROUND: tuple[int, int, int] = (255, 255, 255)
COL_UNVISITED: tuple[int, int, int] = (0, 0, 255)
COL_LINE: tuple[int, int, int] = (0, 0, 0)
COL_START: tuple[int, int, int] = (0, 255, 0)
COL_GOAL: tuple[int, int, int] = (255, 0, 0)
COL_TEXT: tuple[int, int, int] = (192, 192, 192)
COL_TEXT_DROP: tuple[int, int, int] = (64, 64, 64)
LINE_WIDTH: int = 2
LINE_WIDTH_GOAL: int = 5

DEFAULT_STARTPOS: tuple[int, int] = (0, 0)
DEFAULT_SEED = 1234

def RenderStaticTextOverlay(font, randomSeed: int, pos: tuple[int, int]):
    s = f"R: Random seed - G: Check goal - UP: Increase seed - DOWN: Decrease seed - LMB: New start pos - RMB: New goal pos - SPACE: Pause - RETURN: Clear"
    return (font.render(s, True, COL_TEXT), font.render(s, True, COL_TEXT_DROP))

def RenderHUDOverlay(font, randomSeed: int, startPos: tuple[int, int], goalPos: tuple[int, int], showGoal: bool):
    s = f"Seed: {randomSeed}, StartPos: {startPos}, showGoal: {showGoal}, GoalPos: {goalPos}"
    return (font.render(s, True, COL_TEXT), font.render(s, True, COL_TEXT_DROP))

class Maze:
    # Properties a cell in the maze can have
    class CELLFLAGS(enum.IntFlag):
        CLEAR = 0 # Default value
        CELL_PATH_N = enum.auto() # Connected to nothern neighbor
        CELL_PATH_E = enum.auto() # Connected to eastern neighbor
        CELL_PATH_S = enum.auto() # Connected to southern neighbor
        CELL_PATH_W = enum.auto() # Connected to western neighbor
        CELL_VISITED = enum.auto() # Cell has been visited

    # Direction identifiers
    class DIRECTION:
        NORTH = 0
        EAST = 1
        SOUTH = 2
        WEST = 3

    # Directions
    DIRECTIONS = [
        (0, -1),
        (1, 0),
        (0, 1),
        (-1, 0)
    ]

    def __init__(self, width: int, height: int, startPos: tuple[int, int], randomSeed: int):
        """
        Initializes data structures for a new maze.
        """
        # Initialize
        self.width: int = width
        self.height: int = height
        self.size: int = width * height
        self.cells: list[enum.IntFlag] = [Maze.CELLFLAGS.CLEAR for _ in range(self.size)]
        self.visitedCells: int = 0
        self.stack: collections.deque[(int, int)] = collections.deque()
        self.random = random.Random()
        self.random.seed(randomSeed)
        self.goalPath: list[tuple[int, int]] = []
        self.goalFound: bool = False
        self.lastGoalPos: tuple[int, int] = ()

        # Begin
        self.stack.append(startPos)
        self.set_cell(startPos, Maze.CELLFLAGS.CELL_VISITED)
        self.visitedCells = 1

    def get_cell(self, pos: tuple[int, int]):
        """
        Returns the value of a cell by XY coordinate.
        """
        return self.cells[pos[1] * self.width + pos[0]]

    def set_cell(self, pos: tuple[int, int], cell):
        """
        Sets the value of a cell by XY coordinate.
        """
        self.cells[pos[1] * self.width + pos[0]] = cell

    def offset(self, pos: tuple[int, int], off: tuple[int, int]) -> tuple[int, int]:
        """
        Returns a tuple with new coordinates that are offset from
        the current coordinate (which is the top item on the stack).
        """
        return (pos[0] + off[0], pos[1] + off[1])

    def get_unvisited_neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        """
        Returns a list with coordinates of unvisited cells neighbored to 'pos'.
        """
        # Create list of unvisited neighbors
        unvisitedNeighbors = []

        # North neighbor
        if pos[1] > 0 and Maze.CELLFLAGS.CELL_VISITED not in self.get_cell(self.offset(pos, Maze.DIRECTIONS[Maze.DIRECTION.NORTH])):
            unvisitedNeighbors.append(Maze.DIRECTION.NORTH)

        # East neighbor
        if pos[0] < self.width - 1 and Maze.CELLFLAGS.CELL_VISITED not in self.get_cell(self.offset(pos, Maze.DIRECTIONS[Maze.DIRECTION.EAST])):
            unvisitedNeighbors.append(Maze.DIRECTION.EAST)

        # South neighbor
        if pos[1] < self.height - 1 and Maze.CELLFLAGS.CELL_VISITED not in self.get_cell(self.offset(pos, Maze.DIRECTIONS[Maze.DIRECTION.SOUTH])):
            unvisitedNeighbors.append(Maze.DIRECTION.SOUTH)

        # West neighbor
        if pos[0] > 0 and Maze.CELLFLAGS.CELL_VISITED not in self.get_cell(self.offset(pos, Maze.DIRECTIONS[Maze.DIRECTION.WEST])):
            unvisitedNeighbors.append(Maze.DIRECTION.WEST)

        return unvisitedNeighbors

    def advance(self) -> tuple[bool, bool]:
        """
        Advances maze algorithm by one step.
        """
        # If the maze has already been filled completely, abort
        if self.visitedCells >= self.size:
            return False, False

        currentPos = self.stack[-1]

        # Step 1: Create set of unvisited neighbors
        unvisitedNeighbors = self.get_unvisited_neighbors(currentPos)

        # Are there any unvisited neighbors?
        if unvisitedNeighbors:
            # Choose available neighbor at random
            nextCellDir = self.random.choice(unvisitedNeighbors)

            if nextCellDir == Maze.DIRECTION.NORTH:
                neighborPos = self.offset(currentPos, Maze.DIRECTIONS[Maze.DIRECTION.NORTH])
                
                # There's a path to the neighbor
                self.set_cell(currentPos, self.get_cell(currentPos) | Maze.CELLFLAGS.CELL_PATH_N)

                # There's a path from the neighbor, and the neighbor has been visited
                self.set_cell(neighborPos, self.get_cell(neighborPos) | Maze.CELLFLAGS.CELL_PATH_S | Maze.CELLFLAGS.CELL_VISITED)

            elif nextCellDir == Maze.DIRECTION.EAST:
                neighborPos = self.offset(currentPos, Maze.DIRECTIONS[Maze.DIRECTION.EAST])
                
                # There's a path to the neighbor
                self.set_cell(currentPos, self.get_cell(currentPos) | Maze.CELLFLAGS.CELL_PATH_E)

                # There's a path from the neighbor, and the neighbor has been visited
                self.set_cell(neighborPos, self.get_cell(neighborPos) | Maze.CELLFLAGS.CELL_PATH_W | Maze.CELLFLAGS.CELL_VISITED)

            elif nextCellDir == Maze.DIRECTION.SOUTH:
                neighborPos = self.offset(currentPos, Maze.DIRECTIONS[Maze.DIRECTION.SOUTH])
                
                # There's a path to the neighbor
                self.set_cell(currentPos, self.get_cell(currentPos) | Maze.CELLFLAGS.CELL_PATH_S)

                # There's a path from the neighbor, and the neighbor has been visited
                self.set_cell(neighborPos, self.get_cell(neighborPos) | Maze.CELLFLAGS.CELL_PATH_N | Maze.CELLFLAGS.CELL_VISITED)

            elif nextCellDir == Maze.DIRECTION.WEST:
                neighborPos = self.offset(currentPos, Maze.DIRECTIONS[Maze.DIRECTION.WEST])
                
                # There's a path to the neighbor
                self.set_cell(currentPos, self.get_cell(currentPos) | Maze.CELLFLAGS.CELL_PATH_W)

                # There's a path from the neighbor, and the neighbor has been visited
                self.set_cell(neighborPos, self.get_cell(neighborPos) | Maze.CELLFLAGS.CELL_PATH_E | Maze.CELLFLAGS.CELL_VISITED)
            
            # Push neighbor pos to stack, increase visited counter
            self.stack.append(neighborPos)
            self.visitedCells += 1

            return True, True

        else:
            # Backtrack
            self.stack.pop()

        # Still advancing
        return True, False

    def check_goal_reached(self, goalPos: tuple[int, int]) -> bool:
        """
        If the maze has reached the goal position, returns True and
        stores the path from startPos to goalPos.
        """
        # Don't do again if already found
        if self.goalFound and goalPos == self.lastGoalPos:
            return True

        # Find goalPos in stack
        reversedStack = reversed(self.stack)
        path: list[tuple[int, int]] = []
        found = False
        for currentPos in reversedStack:
            if currentPos == goalPos:
                found = True
            if found:
                path.append(currentPos)
        self.goalPath = path
        self.lastGoalPos = goalPos
        self.goalFound = found
        return found

    def draw(self, canvas):
        """
        Draws the maze in its current state.
        """
        for y in range(0, self.height):
            for x in range(0, self.width):
                block_x = x * BLOCK_SIZE
                block_y = y * BLOCK_SIZE
                current_cell = self.get_cell((x, y))
                if Maze.CELLFLAGS.CELL_VISITED in current_cell:
                    rect = pygame.Rect(block_x, block_y, BLOCK_SIZE, BLOCK_SIZE)
                    canvas.fill(COL_BACKGROUND, rect)
                    pass

        for y in range(0, self.height):
            for x in range(0, self.width):
                block_x = x * BLOCK_SIZE
                block_y = y * BLOCK_SIZE
                current_cell = self.get_cell((x, y))
                if not Maze.CELLFLAGS.CELL_VISITED in current_cell:
                    continue

                # East wall
                if not Maze.CELLFLAGS.CELL_PATH_E in current_cell:
                    pygame.draw.line(canvas, COL_LINE, (block_x + BLOCK_SIZE - 1, block_y - 1), (block_x + BLOCK_SIZE - 1, block_y + BLOCK_SIZE - 1), LINE_WIDTH)
                # South wall
                if not Maze.CELLFLAGS.CELL_PATH_S in current_cell:
                    pygame.draw.line(canvas, COL_LINE, (block_x - 1, block_y + BLOCK_SIZE - 1), (block_x + BLOCK_SIZE - 1, block_y + BLOCK_SIZE - 1), LINE_WIDTH)

    def draw_goal_path(self, canvas):
        """
        Draws the goal path, if there is one.
        """
        halfBlockSize = int(BLOCK_SIZE / 2)
        previousPos = None
        for pos in self.goalPath:
            pos = (pos[0] * BLOCK_SIZE + halfBlockSize, pos[1] * BLOCK_SIZE + halfBlockSize)
            if previousPos is not None:
                pygame.draw.line(canvas, COL_GOAL, previousPos, pos, LINE_WIDTH_GOAL)
            previousPos = pos

def main():
    # PyGame
    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE)
    pygame.display.set_caption(SCRIPT_TITLE)
    clock = pygame.time.Clock()

    pygame.font.init()
    font = pygame.font.SysFont(pygame.font.get_default_font(), FONT_SIZE)

    randomSeed = DEFAULT_SEED
    mazeStartPos = DEFAULT_STARTPOS

    mazeWidth = int(SCREEN_SIZE[0] / BLOCK_SIZE)
    mazeHeight = int(SCREEN_SIZE[1] / BLOCK_SIZE)
    mazeGoalPos = (mazeWidth - 1, mazeHeight - 1)
    maze = Maze(mazeWidth, mazeHeight, mazeStartPos, randomSeed)
    screen.fill(COL_UNVISITED)
    staticTextOverlays = RenderStaticTextOverlay(font, randomSeed, mazeStartPos)
    hudTextOverlays = RenderHUDOverlay(font, randomSeed, mazeStartPos, mazeGoalPos, False)

    isRunning = True
    isAdvancing = True
    checkGoal = True
    while isRunning:
        # Event handling
        for event in pygame.event.get():
            # Quit app
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            elif event.type == pygame.KEYDOWN:
                # print(event.key)
                if event.key == 32: # SPACE
                    isAdvancing = not isAdvancing
                elif event.key == 13: #RETURN
                    maze = Maze(mazeWidth, mazeHeight, mazeStartPos, randomSeed)
                    screen.fill(COL_UNVISITED)
                elif event.key == 114: # R
                    randomSeed = random.randint(1, 9999)
                    maze = Maze(mazeWidth, mazeHeight, mazeStartPos, randomSeed)
                    hudTextOverlays = RenderHUDOverlay(font, randomSeed, mazeStartPos, mazeGoalPos, checkGoal)
                elif event.key == 103: # G
                    checkGoal = not checkGoal
                    hudTextOverlays = RenderHUDOverlay(font, randomSeed, mazeStartPos, mazeGoalPos, checkGoal)
                elif event.key == 1073741906: # UP
                    randomSeed += 1
                    maze = Maze(mazeWidth, mazeHeight, mazeStartPos, randomSeed)
                    hudTextOverlays = RenderHUDOverlay(font, randomSeed, mazeStartPos, mazeGoalPos, checkGoal)
                elif event.key == 1073741905: # DOWN
                    randomSeed -= 1
                    maze = Maze(mazeWidth, mazeHeight, mazeStartPos, randomSeed)
                    hudTextOverlays = RenderHUDOverlay(font, randomSeed, mazeStartPos, mazeGoalPos, checkGoal)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mousePos = event.pos
                mazeMousePos = (int(mousePos[0] / BLOCK_SIZE), int(mousePos[1] / BLOCK_SIZE))
                button = event.button
                # Left mouse button down
                if button == 1:
                    mazeStartPos = mazeMousePos
                    maze = Maze(mazeWidth, mazeHeight, mazeStartPos, randomSeed)
                    hudTextOverlays = RenderHUDOverlay(font, randomSeed, mazeStartPos, mazeGoalPos, checkGoal)
                # Right mouse button down
                elif button == 3:
                    mazeGoalPos = mazeMousePos
                    hudTextOverlays = RenderHUDOverlay(font, randomSeed, mazeStartPos, mazeGoalPos, checkGoal)

        # Update and draw maze
        if isAdvancing:
            screen.fill(COL_UNVISITED)
            needsUpdate = False
            while not needsUpdate and isAdvancing:
                isAdvancing, needsUpdate = maze.advance()
            maze.draw(screen)

            halfLineWidth = int(LINE_WIDTH / 2)

            if checkGoal:
                if maze.check_goal_reached(mazeGoalPos):
                    maze.draw_goal_path(screen)
                rect = pygame.Rect(mazeGoalPos[0] * BLOCK_SIZE + halfLineWidth, mazeGoalPos[1] * BLOCK_SIZE + halfLineWidth, BLOCK_SIZE - LINE_WIDTH, BLOCK_SIZE - LINE_WIDTH)
                screen.fill(COL_GOAL, rect)

            rect = pygame.Rect(mazeStartPos[0] * BLOCK_SIZE + halfLineWidth, mazeStartPos[1] * BLOCK_SIZE + halfLineWidth, BLOCK_SIZE - LINE_WIDTH, BLOCK_SIZE - LINE_WIDTH)
            screen.fill(COL_START, rect)

            # Draw text overlays
            screen.blit(hudTextOverlays[1], (11, 11))
            screen.blit(hudTextOverlays[0], (10, 10))
            screen.blit(staticTextOverlays[1], (11, 31))
            screen.blit(staticTextOverlays[0], (10, 30))

        # Update display & tick
        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
