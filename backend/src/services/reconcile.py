"""Reconcile settlement allocations against the work-log ledger (pure functions).

Business rules:

* Several orders may share one work-log entry. Each order receives an explicit
  share; shares of the same serial must add up to the ledger amount.
* Reconciliation is per serial number. A serial is *unresolved* when the ledger
  has no such entry ("没到") or when the shares do not add up ("对不上").
* Orders sharing a serial form one connected group. If any serial in the group
  is unresolved, every order in that group waits — including orders only
  indirectly linked through other shared serials.
* A group switches only when all of its serials reconcile. Orders with no
  allocations are never touched; unrelated orders keep entering the sample.
"""
from collections import defaultdict

TOLERANCE = 1e-6


def _components(allocations, serial_orders):
    """Connected components of the order <-> serial bipartite graph."""
    parent = {}

    def find(node):
        parent.setdefault(node, node)
        root = node
        while parent[root] != root:
            root = parent[root]
        while parent[node] != root:
            parent[node], node = root, parent[node]
        return root

    def union(left, right):
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    for order in allocations:
        find(order)
    for orders in serial_orders.values():
        ordered = sorted(orders)
        for other in ordered[1:]:
            union(ordered[0], other)
    groups = defaultdict(list)
    for order in allocations:
        groups[find(order)].append(order)
    return {root: sorted(members) for root, members in groups.items()}


def reconcile(lines, ledger, committed=None, samples=None):
    """Return per-order and per-serial reconciliation.

    ``lines``      iterable of ``{'order': str, 'serial': str, 'hours': float}``.
    ``ledger``     mapping ``serial -> recorded work-log hours``.
    ``committed``  mapping ``order -> hours written by the latest switch``.
    ``samples``    mapping ``order -> hours currently used by comparison``.
    """
    committed = committed or {}
    samples = samples or {}
    allocations = defaultdict(dict)
    for line in lines:
        # (order, serial) is unique in storage; last write wins so a re-sent
        # allocation never accumulates a second share.
        allocations[line['order']][line['serial']] = float(line['hours'])
    serial_orders = defaultdict(set)
    serial_total = defaultdict(float)
    for order, shares in allocations.items():
        for serial, hours in shares.items():
            serial_orders[serial].add(order)
            serial_total[serial] += hours

    serials = {}
    for serial in sorted(serial_total):
        allocated = serial_total[serial]
        present = serial in ledger
        matched = present and abs(allocated - float(ledger[serial])) <= TOLERANCE
        serials[serial] = {
            'serial': serial,
            'allocated': round(allocated, 6),
            'ledger': round(float(ledger[serial]), 6) if present else None,
            'reason': 'matched' if matched else ('unbalanced' if present else 'missing'),
            'orders': sorted(serial_orders[serial]),
        }

    components = _components(allocations, serial_orders)
    orders = {}
    summary = []
    for members in components.values():
        waiting = sorted({serial for member in members for serial in allocations[member]
                          if serials[serial]['reason'] != 'matched'})
        state = 'waiting' if waiting else 'aligned'
        waiting_detail = [{'serial': serial, 'reason': serials[serial]['reason'],
                           'orders': serials[serial]['orders']} for serial in waiting]
        summary.append({'orders': members, 'state': state, 'waiting_on': waiting})
        for order in members:
            rows = [{
                'serial': serial,
                'allocated': round(allocations[order][serial], 6),
                'ledger': serials[serial]['ledger'],
                'shared_with': sorted(serial_orders[serial] - {order}),
                'reason': serials[serial]['reason'],
            } for serial in sorted(allocations[order])]
            orders[order] = {
                'order': order,
                'state': state,
                'pending_hours': round(sum(allocations[order].values()), 6),
                'sample_hours': samples.get(order),
                'committed_hours': committed.get(order),
                'serials': rows,
                'missing': [row['serial'] for row in rows if row['reason'] == 'missing'],
                'unbalanced': [row['serial'] for row in rows if row['reason'] == 'unbalanced'],
                'waiting_on': waiting,
                'component_waiting': waiting_detail,
                'component': members,
            }

    summary.sort(key=lambda item: item['orders'][0])
    waiting_orders = sorted(order for order, detail in orders.items() if detail['state'] == 'waiting')
    return {
        'orders': orders,
        'serials': serials,
        'components': summary,
        'waiting_orders': waiting_orders,
        'missing_serials': sorted(serial for serial, detail in serials.items()
                                  if detail['reason'] == 'missing'),
        'unbalanced_serials': sorted(serial for serial, detail in serials.items()
                                     if detail['reason'] == 'unbalanced'),
    }
