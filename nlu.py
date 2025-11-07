"""
Natural Language Understanding (NLU) module for parsing robot arm commands.
Converts natural language text into structured JSON action schema.
"""
import re
from pydantic import BaseModel
from typing import Literal, Optional


class Target(BaseModel):
    """Target specification for object selection."""
    type: Literal["color", "label", "nearest"] = "nearest"
    value: Optional[str] = None


class Drop(BaseModel):
    """Drop location specification."""
    mode: Literal["relative", "absolute", "zone"] = "relative"
    dx: float = 0.0  # meters (x right +)
    dy: float = 0.0  # meters (y forward +)
    zone: Optional[str] = None


class Command(BaseModel):
    """Parsed command structure."""
    task: Literal["pick_place", "nudge", "open", "close"] = "pick_place"
    target: Target = Target()
    drop: Drop = Drop()


# Color keywords
COLORS = {"red", "green", "blue", "yellow", "orange", "purple", "black", "white"}

# Direction keywords
LEFT, RIGHT = {"left", "west"}, {"right", "east"}
FWD, BACK = {"forward", "ahead", "up"}, {"back", "backward", "down"}


def _dist(text: str) -> float:
    """
    Parse distance from natural language text.
    
    Supports:
    - "a little/bit/slightly" -> 0.03 meters
    - "N mm/cm/m" -> converted to meters
    
    Args:
        text: Input text to parse
        
    Returns:
        Distance in meters (default: 0.03)
    """
    if re.search(r"\b(little|bit|slight|slightly)\b", text):
        return 0.03
    
    m = re.search(r"(\d+(?:\.\d+)?)\s*(mm|millimeter|cm|centimeter|m|meter)s?\b", text)
    if not m:
        return 0.03
    
    val, unit = float(m.group(1)), m.group(2)
    if unit.startswith("mm"):
        return val / 1000.0
    if unit.startswith("cm"):
        return val / 100.0
    return val


def parse(text: str) -> Command:
    """
    Parse natural language command into structured Command object.
    
    Examples:
        "grab the red one and put it a little to the left"
        "pick red and move 5 cm forward"
        "nudge that 3 cm right"
        "open"
        "close"
    
    Args:
        text: Natural language command string
        
    Returns:
        Parsed Command object
    """
    t = text.lower()
    
    # Parse target (color, label, or nearest)
    tgt = Target()
    for c in COLORS:
        if re.search(rf"\b{c}\b", t):
            tgt = Target(type="color", value=c)
            break
    
    if tgt.type == "nearest":
        # Check for object labels (including bottle variations)
        m = re.search(r"\b(apple|marker|cube|block|cap|screw|bottle|canada dry|canada|soda|drink)\b", t)
        if m:
            label = m.group(1)
            # Map variations to standard labels
            if label in ("canada dry", "canada", "soda", "drink"):
                label = "bottle"
            tgt = Target(type="label", value=label)
    
    # Parse direction and distance
    dx = dy = 0.0
    d = _dist(t)
    
    if any(w in t for w in LEFT):
        dx -= d
    if any(w in t for w in RIGHT):
        dx += d
    if any(w in t for w in FWD):
        dy += d
    if any(w in t for w in BACK):
        dy -= d
    
    # Parse task type
    if re.search(r"\b(nudge|move|shift)\b", t) and not re.search(r"\b(grab|pick|take)\b", t):
        return Command(task="nudge", target=tgt, drop=Drop(mode="relative", dx=dx, dy=dy))
    
    if re.search(r"\bopen\b", t):
        return Command(task="open")
    
    if re.search(r"\bclose\b", t):
        return Command(task="close")
    
    return Command(task="pick_place", target=tgt, drop=Drop(mode="relative", dx=dx, dy=dy))

