"""把 SUMO 路网转换为本项目的"空间单元 + 邻接"场景配置。

依据 [Lane D 验证报告](../../docs/verify/lane-d-sumo-cityflow-abstreet.md) §6 的映射表：

    SUMO edge          -> 空间单元 u_i
    edge from/to       -> 有向邻接 (i,j) ∈ E
    edge.length        -> 通行成本 c_ij 的基础
    edge.speed         -> 与长度结合折算通行成本
    edge.numLanes      -> 容量 C_i 的物理代理

用法：
    py -3.13 scripts/sumo_to_units.py <net.xml> -o configs/scenarios/from_sumo.json

需要 sumolib（`pip install sumolib`）。若本机已安装 SUMO 二进制，
sumolib 会自动定位；也可设 SUMO_HOME 环境变量。
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    import sumolib
except ImportError:  # pragma: no cover
    print("错误：需要 sumolib。请运行： pip install sumolib", file=sys.stderr)
    raise SystemExit(2)


#: 每个标准车道的近似容纳车辆数（用于把 lanes 换算为容量人次）
VEHICLES_PER_LANE = 40.0
#: 步行速度（m/s），用于把路段长度换算为通行时间成本
WALK_SPEED = 1.34


def norm_positions(net) -> dict[str, tuple[float, float]]:
    """把节点坐标归一化到 [0,1]，便于前端可视化。"""
    xs, ys = [], []
    for n in net.getNodes():
        x, y = n.getCoord()
        xs.append(x)
        ys.append(y)
    if not xs:
        return {}
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    spanx = (maxx - minx) or 1.0
    spany = (maxy - miny) or 1.0
    return {n.getID(): ((n.getCoord()[0] - minx) / spanx,
                        (n.getCoord()[1] - miny) / spany)
            for n in net.getNodes()}


def classify(edge) -> str:
    """依据车道数与速度粗判单元类型。"""
    speed = edge.getSpeed()
    if edge.getLaneNumber() <= 1 and speed < 7.0:
        return "corridor"
    if speed >= 13.0:
        return "corridor"
    return "stay"


def convert(net_path: Path, *, min_length: float = 1.0) -> dict:
    net = sumolib.net.readNet(str(net_path))
    positions = norm_positions(net)

    # 入口/出口判定：SUMO 路网的边界路段
    #   entry：起点节点入度为 0（外部进入）
    #   exit ：终点节点出度为 0（离开场地）
    in_deg: dict[str, int] = {}
    out_deg: dict[str, int] = {}
    for e in net.getEdges(withInternal=False):
        out_deg[e.getFromNode().getID()] = out_deg.get(e.getFromNode().getID(), 0) + 1
        in_deg[e.getToNode().getID()] = in_deg.get(e.getToNode().getID(), 0) + 1

    units: list[dict] = []
    edge_to_unit: dict[str, str] = {}
    skipped = 0

    for e in net.getEdges(withInternal=False):
        eid = e.getID()
        length = e.getLength()
        if length < min_length:
            skipped += 1
            continue
        speed = max(e.getSpeed(), 0.1)
        lanes = e.getLaneNumber()
        from_node = e.getFromNode().getID()
        to_node = e.getToNode().getID()
        x, y = positions.get(from_node, (0.5, 0.5))

        # 通行时间成本（以步速折算）
        t_walk = length / WALK_SPEED
        # 容量：车道数 × 单位容纳量，按长度缩放
        capacity = max(10.0, lanes * VEHICLES_PER_LANE * min(2.0, length / 100.0))

        is_entry = in_deg.get(from_node, 0) == 0
        is_exit = out_deg.get(to_node, 0) == 0
        if is_entry:
            unit_type = "entry"
        elif is_exit:
            unit_type = "exit"
        else:
            unit_type = classify(e)

        unit: dict = {
            "id": f"e_{eid}",
            "name": f"{eid} ({from_node}->{to_node})",
            "type": unit_type,
            "area": round(length * 3.5 * lanes, 2),   # 面积近似：长 × 单车道宽 × 车道数
            "capacity": round(capacity, 1),
            "attract": 1.0,
            "mobility": 0.35 if lanes > 1 else 0.2,
            "x": round(x, 4),
            "y": round(y, 4),
            "_sumo": {
                "edge_id": eid,
                "length_m": round(length, 2),
                "speed_ms": round(speed, 3),
                "lanes": lanes,
                "walk_time_s": round(t_walk, 2),
                "is_entry": is_entry,
                "is_exit": is_exit,
            },
        }
        if is_exit:
            # 出口单元赋予离开倾向，使系统能向外流出
            unit["exit_rate"] = 0.1
        edge_to_unit[eid] = unit["id"]
        units.append(unit)

    # 邻接：两条边共享节点即视为可达（e 的终点 == cand 的起点）
    # 用 node -> 出边 索引把复杂度从 O(E²) 降到 O(E)
    out_by_node: dict[str, list] = {}
    for cand in net.getEdges(withInternal=False):
        out_by_node.setdefault(cand.getFromNode().getID(), []).append(cand)

    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for e in net.getEdges(withInternal=False):
        src = edge_to_unit.get(e.getID())
        if src is None:
            continue
        for cand in out_by_node.get(e.getToNode().getID(), []):
            if cand is e:
                continue
            dst = edge_to_unit.get(cand.getID())
            if dst is None or (src, dst) in seen:
                continue
            seen.add((src, dst))
            # 成本：以步速折算的目标路段通行时间，缩放到常用量级区间
            cost = round(max(0.5, cand.getLength() / WALK_SPEED / 6.0), 3)
            edges.append({"src": src, "dst": dst, "cost": cost})

    return {
        "meta": {
            "name": f"由 SUMO 路网转换：{net_path.name}",
            "source": str(net_path),
            "generator": "scripts/sumo_to_units.py",
            "units_count": len(units),
            "skipped_short_edges": skipped,
            "mapping_note": (
                "SUMO edge -> 空间单元；from/to -> 邻接；length/speed/lanes -> "
                "成本与容量的物理代理。容量与成本为近似换算，正式实验须实测标定。"
            ),
        },
        "units": units,
        "edges": edges,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="把 SUMO 路网转换为本项目场景配置")
    ap.add_argument("net", type=Path, help="SUMO net.xml 路径")
    ap.add_argument("-o", "--out", type=Path, required=True, help="输出场景 JSON 路径")
    ap.add_argument("--min-length", type=float, default=1.0,
                    help="短于此长度的边将被跳过（米，默认 1.0）")
    args = ap.parse_args(argv)

    if not args.net.exists():
        print(f"错误：找不到 {args.net}", file=sys.stderr)
        return 2

    spec = convert(args.net, min_length=args.min_length)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"转换完成：{args.out}")
    print(f"  单元数: {len(spec['units'])}")
    print(f"  邻接边数: {len(spec['edges'])}")
    if spec["meta"]["skipped_short_edges"]:
        print(f"  跳过过短边: {spec['meta']['skipped_short_edges']}")

    # 结构自检：若本仓库的 src 可用，直接校验生成场景能否被内核加载
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from src.core import SpaceGraph
        g = SpaceGraph.from_dict(spec)
        problems = g.validate()
        print(f"  内核加载自检: {len(g)} 单元 / {int(g.adjacency.sum())} 边")
        if problems:
            print("  结构告警:")
            for p in problems:
                print(f"    - {p}")
        else:
            print("  结构自检通过")
    except Exception as exc:  # noqa: BLE001
        print(f"  (跳过内核自检: {type(exc).__name__}: {exc})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
