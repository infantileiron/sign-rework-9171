import unittest

from src.services.reconcile import reconcile


def line(order, serial, hours):
    return {'order': order, 'serial': serial, 'hours': hours}


class ReconciliationTest(unittest.TestCase):
    def test_shared_serial_counts_once(self):
        state = reconcile([line('A', 'S1', 4.0), line('B', 'S1', 3.0)], {'S1': 7.0})
        self.assertEqual(state['serials']['S1']['allocated'], 7.0)
        self.assertEqual(state['waiting_orders'], [])
        self.assertEqual(state['orders']['A']['pending_hours'], 4.0)
        self.assertEqual(state['orders']['B']['serials'][0]['shared_with'], ['A'])

    def test_missing_serial_blocks_every_shared_order(self):
        state = reconcile([line('A', 'S1', 1.0), line('B', 'S1', 1.0), line('B', 'S2', 2.0)],
                          {'S1': 2.0})
        self.assertEqual(state['missing_serials'], ['S2'])
        self.assertEqual(state['waiting_orders'], ['A', 'B'])
        self.assertEqual(state['components'], [
            {'orders': ['A', 'B'], 'state': 'waiting', 'waiting_on': ['S2']},
        ])

    def test_indirect_chain_waits(self):
        state = reconcile([line('A', 'S1', 1.0), line('B', 'S1', 1.0),
                           line('B', 'S2', 1.0), line('C', 'S2', 1.0),
                           line('D', 'S3', 1.0)], {'S1': 2.0, 'S3': 1.0})
        self.assertEqual(state['waiting_orders'], ['A', 'B', 'C'])
        self.assertEqual(state['orders']['D']['state'], 'aligned')
        self.assertEqual(state['orders']['C']['component'], ['A', 'B', 'C'])

    def test_unbalanced_share_keeps_group_waiting(self):
        state = reconcile([line('A', 'S1', 1.0), line('B', 'S1', 1.5)], {'S1': 2.0})
        self.assertEqual(state['unbalanced_serials'], ['S1'])
        self.assertEqual(state['waiting_orders'], ['A', 'B'])

    def test_duplicate_line_does_not_double_count(self):
        state = reconcile([line('A', 'S1', 1.0), line('A', 'S1', 1.0)], {'S1': 1.0})
        self.assertEqual(state['orders']['A']['pending_hours'], 1.0)
        self.assertEqual(state['serials']['S1']['reason'], 'matched')

    def test_unrelated_order_stays_aligned(self):
        state = reconcile([line('A', 'S1', 1.0), line('B', 'S2', 2.0)], {'S1': 1.0})
        self.assertEqual(state['orders']['A']['state'], 'aligned')
        self.assertEqual(state['orders']['B']['state'], 'waiting')
        self.assertEqual(state['orders']['B']['missing'], ['S2'])


if __name__ == '__main__':
    unittest.main()
