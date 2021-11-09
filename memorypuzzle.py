import random, pygame, sys
from pygame.locals import *

FPS = 30
WINDOWWIDTH = 640
WINDOWHEIGHT = 480
REVEALSPEED = 8 # speed boxes' sliding reveals and covers
BOXSIZE = 40
GAPSIZE = 10
BOARDWIDTH = 10 # number of columns of icons
BOARDHEIGHT = 7 # number of rows of icons
assert (BOARDWIDTH * BOARDHEIGHT) % 2 == 0, 'Board needs to have an even number of boxes for pairs of matches'
XMARGIN = int((WINDOWWIDTH - (BOARDWIDTH * (BOXSIZE + GAPSIZE))) / 2)
YMARGIN = int((WINDOWHEIGHT - (BOARDHEIGHT * (BOXSIZE + GAPSIZE))) / 2)

# setup colors
BLACK       = (  0,   0,   0)
WHITE       = (255, 255, 255)
RED         = (255,   0,   0)
GREEN       = (  0, 255,   0)
BLUE        = (  0,   0, 255)
GRAY        = (100, 100, 100)
NAVYBLUE    = ( 60,  60, 100)
YELLOW      = (255, 255,   0)
ORANGE      = (255, 128,   0)
PURPLE      = (255,   0, 255)
CYAN        = (  0, 255, 255)

BGCOLOR = NAVYBLUE
LIGHTBGCOLOR = GRAY
BOXCOLOR = WHITE
HIGHLIGHTCOLOR = BLUE

DONUT = 'donut'
SQUARE = 'square'
DIAMOND = 'diamond'
LINES = 'lines'
OVAL = 'oval'

ALLCOLORS = (RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, CYAN)
ALLSHAPES = (DONUT, SQUARE, DIAMOND, LINES, OVAL)
assert len(ALLCOLORS) * len(ALLSHAPES) * 2 >= BOARDWIDTH * BOARDHEIGHT, "Board is too big for the number of shapes/colors defined."

def main():
    global FPSCLOCK, DISPLAYSURF
    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))

    mouseX = mouseY = 0
    pygame.display.set_caption("Memory game")

    mainBoard = getRandomizedBoard()
    revealedBoxes = generateRevealedBoxesData(False)

    firstSelection = None # stores (x, y) of the first box clicked

    DISPLAYSURF.fill(BGCOLOR)
    startGameAnimation(mainBoard)

    while True:
        mouseClicked = False
        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(mainBoard, revealedBoxes)

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEMOTION:
                mouseX, mouseY = event.pos
            elif event.type == MOUSEBUTTONUP:
                mouseX, mouseY = event.pos
                mouseClicked = True
        boxX, boxY = getBoxAtPixel(mouseX, mouseY)
        if boxX != None and boxY != None:
            # The mouse is currently over a box
            if not revealedBoxes[boxX][boxY]:
                drawHighlightBox(boxX, boxY)
            if not revealedBoxes[boxX][boxY] and mouseClicked:
                revealBoxesAnimation(mainBoard, [(boxX, boxY)])
                revealedBoxes[boxX][boxY] = True
                if firstSelection == None: # the current box was the first clicked
                    firstSelection = (boxX, boxY)
                else: # the current box is the second one clicked
                    # Check if there is a match between the two icons
                    icon1shape, icon1color = getShapeAndColor(mainBoard, firstSelection[0], firstSelection[1])
                    icon2shape, icon2color = getShapeAndColor(mainBoard, boxX, boxY)
                    if icon1shape != icon2shape or icon1color != icon2color:
                        # icons don't match. Recover up both selections
                        pygame.time.wait(1000) # wait for 1 sec
                        coverBoxesAnimation(mainBoard, [(firstSelection[0], firstSelection[1]), (boxX, boxY)])
                        revealedBoxes[firstSelection[0]][firstSelection[1]] = False
                        revealedBoxes[boxX][boxY] = False
                    elif hasWon(revealedBoxes): # if all pairs are found
                        gameWonAnimation(mainBoard)
                        pygame.time.wait(2000)
                        # Reset the board
                        mainBoard = getRandomizedBoard()
                        revealedBoxes = generateRevealedBoxesData(False)
                        # Show fully unrevealed board for a second
                        drawBoard(mainBoard, revealedBoxes)
                        pygame.display.update()
                        pygame.time.wait(1000)
                        # Replay the start game animation
                        startGameAnimation(mainBoard)
                    firstSelection = None # reset
        pygame.display.update()
        FPSCLOCK.tick(FPS)


def generateRevealedBoxesData(val: bool):
    "Generate array initialized with val"
    revealedBoxes = []
    for i in range(BOARDWIDTH):
        revealedBoxes.append([val] * BOARDHEIGHT)
    
    return revealedBoxes


def getRandomizedBoard():
    "Get a list of every possible shape in every possible color"
    icons = []
    for color in ALLCOLORS:
        for shape in ALLSHAPES:
            icons.append( (shape, color) )
    
    random.shuffle(icons)
    numIconsUsed = int(BOARDWIDTH * BOARDHEIGHT / 2) # how many icons are needed
    icons = icons[:numIconsUsed] * 2
    random.shuffle(icons)

    board = []
    for x in range(BOARDWIDTH):
        column = []
        for y in range(BOARDHEIGHT):
            column.append(icons.pop())
        board.append(column)
    
    return board


def startGameAnimation(board):
    "Randomly reveal the boxes 8 at a time"
    coveredBoxes = generateRevealedBoxesData(False)
    boxes = []
    for x in range(BOARDWIDTH):
        for y in range(BOARDHEIGHT):
            boxes.append( (x, y) )
    random.shuffle(boxes)
    boxGroups = splitIntoGroupsOf(8, boxes)
    drawBoard(board, coveredBoxes)
    for group in boxGroups:
        revealBoxesAnimation(board, group)
        coverBoxesAnimation(board, group)


def splitIntoGroupsOf(groupSize, theList):
    "Splits a list into a list of lists, where the inner lists have groupSize number of items at most"
    result = []
    for i in range(0, len(theList), groupSize):
        result.append(theList[i : i+groupSize])
    return result

def drawBoard(board, revealed):
    "Draws all of the boxes in their covered or revealed state"
    for boxx in range(BOARDWIDTH):
        for boxy in range(BOARDHEIGHT):
            left, top = leftTopCoordsOfBox(boxx, boxy)
            if not revealed[boxx][boxy]:
                # Draw a covered box
                pygame.draw.rect(DISPLAYSURF, BOXCOLOR, (left, top, BOXSIZE, BOXSIZE))
            else:
                # draw revealed icon
                shape, color = getShapeAndColor(board, boxx, boxy)
                drawIcon(shape, color, boxx, boxy)


def leftTopCoordsOfBox(boxx, boxy):
    "Convert board coordinates to screen coordinates"
    left = boxx * (BOXSIZE + GAPSIZE) + XMARGIN
    top = boxy * (BOXSIZE + GAPSIZE) + YMARGIN
    return (left, top)


def drawIcon(shape, color, boxx, boxy):
    quarter = int(BOXSIZE * 0.25)
    half = int(BOXSIZE * 0.5)
    left, top = leftTopCoordsOfBox(boxx, boxy)
    if shape == DONUT:
        pygame.draw.circle(DISPLAYSURF, color, (left+half, top+half), half-5)
        pygame.draw.circle(DISPLAYSURF, BGCOLOR, (left+half, top+half), quarter-5)
    elif shape == SQUARE:
        pygame.draw.rect(DISPLAYSURF, color, (left+quarter, top+quarter, BOXSIZE-half, BOXSIZE-half))
    elif shape == DIAMOND:
        pygame.draw.polygon(DISPLAYSURF, color, (
                                                 (left+half, top), 
                                                 (left+BOXSIZE-1, top+half), 
                                                 (left+half, top+BOXSIZE-1), 
                                                 (left, top+half)
                                                ))
    elif shape == LINES:
        for i in range(0, BOXSIZE, 4):
            pygame.draw.line(DISPLAYSURF, color, (left, top+i), (left+i, top))
            pygame.draw.line(DISPLAYSURF, color, (left+i, top+BOXSIZE-1), (left+BOXSIZE-1, top+i))
    elif shape == OVAL:
        pygame.draw.ellipse(DISPLAYSURF, color, (left, top+quarter, BOXSIZE, half))


def getBoxAtPixel(x, y):
    "Converts screen coords into box coords"
    for boxx in range(BOARDWIDTH):
        for boxy in range(BOARDHEIGHT):
            left, top = leftTopCoordsOfBox(boxx, boxy)
            boxRect = pygame.Rect(left, top, BOXSIZE, BOXSIZE)
            if boxRect.collidepoint(x, y):
                return (boxx, boxy)
    # otherwise
    return (None, None)


def drawHighlightBox(boxX, boxY):
    left, top = leftTopCoordsOfBox(boxX, boxY)
    pygame.draw.rect(DISPLAYSURF, HIGHLIGHTCOLOR, (left-5, top-5, BOXSIZE+10, BOXSIZE+10), 4)


def revealBoxesAnimation(board, boxesToReveal):
    for coverage in range(BOXSIZE, (-REVEALSPEED)-1, -REVEALSPEED):
        drawBoxCovers(board, boxesToReveal, coverage)


def drawBoxCovers(board, boxes, coverage):
    """
    Draw boxes being covered/revealed. 
    board: Array of Arrays of (shape, color) tuple
        is the game board
    boxes: [[int, int]]
        is a list of two-item lists, which have x & y spot of the box
    coverage: 
    """
    for box in boxes:
        left, top = leftTopCoordsOfBox(box[0], box[1])
        pygame.draw.rect(DISPLAYSURF, BGCOLOR, (left, top, BOXSIZE, BOXSIZE))
        shape, color = getShapeAndColor(board, box[0], box[1])
    pass

def getShapeAndColor(board, x, y):
    """
    Returns a tuple of (shape, color)
    board: Array of Arrays of (shape, color) tuple
        is the game board
    x: int
        x coordinate in boxes (not pixels)
    y: int
        y coordinate in boxes (not pixels)
    """
    # TODO: write the func
    return (None, None)


def coverBoxesAnimation(board, boxesToCover):
    # TODO: write the procedure
    pass


def hasWon(revealedBoxes) -> bool:
    "Returns True if all the boxes have been revealed, otherwise False"
    # TODO: write the func
    return False


def gameWonAnimation(board):
    "Flash background color when the player has won"
    # TODO: write the procedure
    pass


if __name__ == "__main__":
    main()