from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from core.grid import EXIT, Grid
from core.rules import in_orthogonal_range, in_power_scan, in_straight_sight, manhattan

Pos = Tuple[int, int]
Action = str
ProbMap = Dict[Pos, float]

_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def _walkable_cells(grid: Grid) -> List[Pos]:
    cells: List[Pos] = []
    for r in range(grid.rows):
        for c in range(grid.cols):
            if grid.is_walkable(r, c):
                cells.append((r, c))
    return cells


def _normalize(prob_map: ProbMap) -> ProbMap:
    total = sum(prob_map.values())
    if total <= 0:
        return prob_map
    return {k: v / total for k, v in prob_map.items()}


def init_guard_probability_map(grid: Grid, guard_pos: Pos) -> ProbMap:
    """Initialize a uniform belief over all walkable cells except Guard's cell."""
    cells = _walkable_cells(grid)
    candidates = [p for p in cells if p != guard_pos]
    if not candidates:
        return {guard_pos: 1.0}
    w = 1.0 / len(candidates)
    return {p: w for p in candidates}


def _predict_rajakar_motion(grid: Grid, prior: ProbMap) -> ProbMap:
    """One-step prediction: Rajakar may move to neighbors or wait."""
    nxt: ProbMap = {}
    for pos, mass in prior.items():
        if mass <= 0:
            continue
        moves = _legal_moves(grid, pos)
        dests = moves + [pos]  # Rajakar can WAIT.
        share = mass / len(dests)
        for d in dests:
            nxt[d] = nxt.get(d, 0.0) + share
    return _normalize(nxt)


def _apply_mask(prob_map: ProbMap, keep_fn: Callable[[Pos], bool]) -> ProbMap:
    out: ProbMap = {}
    for pos, mass in prob_map.items():
        out[pos] = mass if keep_fn(pos) else 0.0
    return _normalize(out)


def update_guard_probability_map(
    grid: Grid,
    prior: ProbMap,
    guard_pos: Pos,
    heard: bool,
    noise_radius: int,
    seen: bool,
    seen_pos: Optional[Pos],
    power_used: bool,
    sight_range: int,
    scan_radius: int,
) -> ProbMap:
    """Update guard belief with motion prediction and current turn observations."""
    if seen and seen_pos is not None:
        return {seen_pos: 1.0}

    belief = _predict_rajakar_motion(grid, prior)

    # Not seen in always-on orthogonal vision -> remove those cells.
    belief = _apply_mask(
        belief,
        lambda p: not in_orthogonal_range(guard_pos, p, sight_range),
    )

    # If scanner was used and still unseen, remove scanner rays too.
    if power_used:
        belief = _apply_mask(
            belief,
            lambda p: not in_power_scan(guard_pos, p, scan_radius),
        )

    # Apply noise evidence from Rajakar's last action.
    if noise_radius > 0:
        if heard:
            belief = _apply_mask(
                belief,
                lambda p: manhattan(guard_pos, p) <= noise_radius,
            )
        else:
            belief = _apply_mask(
                belief,
                lambda p: manhattan(guard_pos, p) > noise_radius,
            )

    # Recovery fallback if evidence becomes over-constrained.
    if sum(belief.values()) <= 0:
        return init_guard_probability_map(grid, guard_pos)
    return belief


def choose_guard_probability_action(
    grid: Grid,
    guard_pos: Pos,
    prob_map: ProbMap,
    last_guard_pos: Optional[Pos] = None,
) -> Tuple[Action, Pos]:
    """Move toward highest-likelihood Rajakar region while reducing back-and-forth loops."""
    legal_moves = _legal_moves(grid, guard_pos)
    if not legal_moves:
        return "WAIT", guard_pos

    best_prob = max(prob_map.values()) if prob_map else 0.0
    hot_cells = [p for p, v in prob_map.items() if v >= best_prob - 1e-12]
    if not hot_cells:
        hot_cells = [guard_pos]

    def local_density(pos: Pos) -> float:
        r, c = pos
        vals = [prob_map.get((r, c), 0.0)]
        for dr, dc in _DIRS:
            vals.append(prob_map.get((r + dr, c + dc), 0.0))
        return sum(vals)

    best_move = legal_moves[0]
    best_score = -1e12
    for m in legal_moves:
        min_d = min(manhattan(m, h) for h in hot_cells)
        score = 0.0
        score += prob_map.get(m, 0.0) * 12.0
        score += local_density(m) * 8.0
        score -= min_d * 3.0
        if last_guard_pos is not None and m == last_guard_pos:
            score -= 2.2
        if score > best_score:
            best_score = score
            best_move = m

    return "MOVE", best_move


def _legal_moves(grid: Grid, pos: Pos) -> List[Pos]:
    r, c = pos
    out: List[Pos] = []
    for dr, dc in _DIRS:
        nr, nc = r + dr, c + dc
        if grid.is_walkable(nr, nc):
            out.append((nr, nc))
    return out


def _nearest_exit_distance(grid: Grid, pos: Pos) -> int:
    exits = grid.all_cells_of_type(EXIT)
    if not exits:
        return 999
    return min(manhattan(pos, ex) for ex in exits)


def _guard_heuristic(
    grid: Grid,
    guard_pos: Pos,
    raj_pos: Optional[Pos],
    sight_range: int,
) -> float:
    if raj_pos is None:
        return _guard_unknown_heuristic(grid, guard_pos)

    dist_gr = manhattan(guard_pos, raj_pos)
    dist_re = _nearest_exit_distance(grid, raj_pos)

    score = 0.0
    score += max(0, 12 - dist_gr) * 8.0
    score -= max(0, 10 - dist_re) * 5.0

    if in_straight_sight(grid, guard_pos, raj_pos, sight_range):
        score += 22.0

    return score


def _guard_unknown_heuristic(grid: Grid, guard_pos: Pos) -> float:
    # When Rajakar is unseen, patrol toward exits to deny escape zones.
    dist_ge = _nearest_exit_distance(grid, guard_pos)
    score = 0.0
    score += max(0, 10 - dist_ge) * 5.0
    score += len(_legal_moves(grid, guard_pos)) * 0.2
    return score


def _apply_action(
    grid: Grid,
    actor: str,
    guard_pos: Pos,
    raj_pos: Pos,
    action: Action,
) -> Tuple[Pos, Pos]:
    if actor == "Guard":
        if action.startswith("MOVE:"):
            dr, dc = map(int, action.split(":", 1)[1].split(","))
            nr, nc = guard_pos[0] + dr, guard_pos[1] + dc
            if grid.is_walkable(nr, nc):
                return (nr, nc), raj_pos
        return guard_pos, raj_pos

    if action.startswith("MOVE:"):
        dr, dc = map(int, action.split(":", 1)[1].split(","))
        nr, nc = raj_pos[0] + dr, raj_pos[1] + dc
        if grid.is_walkable(nr, nc):
            return guard_pos, (nr, nc)
    return guard_pos, raj_pos


def _guard_actions(grid: Grid, guard_pos: Pos) -> List[Action]:
    acts: List[Action] = []
    for nr, nc in _legal_moves(grid, guard_pos):
        dr = nr - guard_pos[0]
        dc = nc - guard_pos[1]
        acts.append(f"MOVE:{dr},{dc}")
    return acts


def _raj_actions(grid: Grid, raj_pos: Pos) -> List[Action]:
    acts: List[Action] = []
    for nr, nc in _legal_moves(grid, raj_pos):
        dr = nr - raj_pos[0]
        dc = nc - raj_pos[1]
        acts.append(f"MOVE:{dr},{dc}")
    acts.append("WAIT")
    if grid.get(*raj_pos) == EXIT:
        acts.append("ESCAPE")
    return acts


def _terminal_after_action(
    grid: Grid,
    actor: str,
    action: Action,
    guard_pos: Pos,
    raj_pos: Pos,
    turn_count: int,
    max_turns: int,
) -> Optional[str]:
    if manhattan(guard_pos, raj_pos) == 1:
        return "Guard"
    if actor == "Rajakar" and action == "ESCAPE" and grid.get(*raj_pos) == EXIT:
        return "Rajakar"
    if turn_count >= max_turns:
        return "Draw"
    return None


def choose_guard_minimax_action(
    grid: Grid,
    guard_pos: Pos,
    raj_pos: Optional[Pos],
    turn_count: int,
    max_turns: int,
    sight_range: int,
    depth: int = 3,
) -> Tuple[Action, Pos]:
    """Return the Guard action chosen by depth-limited minimax with alpha-beta pruning."""

    legal_moves = _legal_moves(grid, guard_pos)

    if raj_pos is None:
        if legal_moves:
            best_move = legal_moves[0]
            best_value = _guard_unknown_heuristic(grid, best_move)
            for m in legal_moves[1:]:
                value = _guard_unknown_heuristic(grid, m)
                if value > best_value:
                    best_value = value
                    best_move = m
            return "MOVE", best_move
        return "WAIT", guard_pos

    def minimax(
        gpos: Pos,
        rpos: Pos,
        actor: str,
        turn: int,
        ply: int,
        alpha: float,
        beta: float,
    ) -> float:
        if ply == 0:
            return _guard_heuristic(grid, gpos, rpos, sight_range)

        actions = _guard_actions(grid, gpos) if actor == "Guard" else _raj_actions(grid, rpos)
        if not actions:
            return _guard_heuristic(grid, gpos, rpos, sight_range)

        if actor == "Guard":
            best = -1e12
            for act in actions:
                ng, nr = _apply_action(grid, actor, gpos, rpos, act)
                winner = _terminal_after_action(grid, actor, act, ng, nr, turn + 1, max_turns)
                if winner == "Guard":
                    value = 10000.0 + ply
                elif winner == "Rajakar":
                    value = -10000.0 - ply
                elif winner == "Draw":
                    value = _guard_heuristic(grid, ng, nr, sight_range)
                else:
                    value = minimax(ng, nr, "Rajakar", turn + 1, ply - 1, alpha, beta)

                if value > best:
                    best = value
                if best > alpha:
                    alpha = best
                if beta <= alpha:
                    break
            return best

        best = 1e12
        for act in actions:
            ng, nr = _apply_action(grid, actor, gpos, rpos, act)
            winner = _terminal_after_action(grid, actor, act, ng, nr, turn + 1, max_turns)
            if winner == "Guard":
                value = 10000.0 + ply
            elif winner == "Rajakar":
                value = -10000.0 - ply
            elif winner == "Draw":
                value = _guard_heuristic(grid, ng, nr, sight_range)
            else:
                value = minimax(ng, nr, "Guard", turn + 1, ply - 1, alpha, beta)

            if value < best:
                best = value
            if best < beta:
                beta = best
            if beta <= alpha:
                break
        return best

    best_action = "WAIT"
    best_value = -1e12

    for act in _guard_actions(grid, guard_pos):
        ng, nr = _apply_action(grid, "Guard", guard_pos, raj_pos, act)
        winner = _terminal_after_action(grid, "Guard", act, ng, nr, turn_count + 1, max_turns)

        if winner == "Guard":
            value = 10000.0
        elif winner == "Rajakar":
            value = -10000.0
        elif winner == "Draw":
            value = _guard_heuristic(grid, ng, nr, sight_range)
        else:
            value = minimax(ng, nr, "Rajakar", turn_count + 1, depth - 1, -1e12, 1e12)

        if value > best_value:
            best_value = value
            best_action = act

    if best_action.startswith("MOVE:"):
        dr, dc = map(int, best_action.split(":", 1)[1].split(","))
        return "MOVE", (guard_pos[0] + dr, guard_pos[1] + dc)

    # Avoid idling on EXIT when movement is possible.
    if grid.get(*guard_pos) == EXIT and legal_moves:
        return "MOVE", legal_moves[0]

    return "WAIT", guard_pos


def _clamp(v: float) -> float:
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


def choose_rajakar_fuzzy_action(
    grid: Grid,
    raj_pos: Pos,
    guard_pos: Optional[Pos],
    clues: Dict[str, bool],
    visit_counts: Optional[Dict[Pos, int]] = None,
) -> Tuple[Action, Pos]:
    """Choose Rajakar action using fuzzy danger rules without exit-map knowledge."""
    moves = _legal_moves(grid, raj_pos)
    if visit_counts is None:
        visit_counts = {}

    # Candidate actions: all legal moves + wait + escape (if valid).
    candidates: List[Tuple[Action, Pos]] = [("WAIT", raj_pos)]
    candidates.extend(("MOVE", p) for p in moves)
    if grid.get(*raj_pos) == EXIT:
        candidates.append(("ESCAPE", raj_pos))

    curr_guard_dist = manhattan(raj_pos, guard_pos) if guard_pos is not None else None
    seen_bonus = 1.0 if clues.get("seen", False) else 0.0
    heard_bonus = 0.6 if clues.get("heard", False) else 0.0
    compelled_revisit = bool(moves) and all(visit_counts.get(p, 0) > 0 for p in moves)

    best = ("WAIT", raj_pos)
    best_score = -1e12

    for action, next_pos in candidates:
        guard_dist = manhattan(next_pos, guard_pos) if guard_pos is not None else None
        near_guard = _clamp((4.0 - guard_dist) / 4.0) if guard_dist is not None else 0.0
        far_guard = _clamp((guard_dist - 2.0) / 6.0) if guard_dist is not None else 0.0

        danger = max(near_guard, seen_bonus, heard_bonus)
        moving_away_from_guard = (
            guard_dist is not None
            and curr_guard_dist is not None
            and guard_dist > curr_guard_dist
        )

        score = 0.0

        # Rule: Immediate escape dominates when possible.
        if action == "ESCAPE" and grid.get(*next_pos) == EXIT:
            score += 10.0 + (1.0 - danger)

        if action == "MOVE":
            # Rule: If danger is high, prioritize creating distance from guard.
            if moving_away_from_guard:
                score += danger * 4.5 + far_guard * 2.0
            else:
                score -= danger * 2.5

            # With unknown door positions, prefer exploration when not in danger.
            score += (1.0 - danger) * 0.8

            # Avoid revisiting cells; only relax when every move is already revisiting.
            visits = visit_counts.get(next_pos, 0)
            if visits == 0:
                score += 3.0
            else:
                revisit_penalty = 3.0 + 1.5 * visits
                if compelled_revisit:
                    revisit_penalty *= 0.35
                score -= revisit_penalty

            # Strong penalty for standing adjacent to the guard.
            if guard_dist is not None and guard_dist <= 1:
                score -= 8.0

        if action == "WAIT":
            score += (1.0 - danger) * 0.4
            score -= danger * 1.6
            score -= 2.0 + 0.5 * visit_counts.get(raj_pos, 0)

        if score > best_score:
            best_score = score
            best = (action, next_pos)

    return best
