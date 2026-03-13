# -*- coding: utf-8 -*-
"""
@author: Hao Wang
@file:   node.py
"""
import random
from .rtable import Router
from .energy import EnergyModel
from .mobility import MobilityModel
from .utils import time2list
from datetime import datetime, timedelta


class Node:

    def __init__(self, net, name, tle, index):
        super(Node, self).__init__()
        self.net = net

        self.name = name
        self.tle = tle
        self.index = index

        self.mobile = MobilityModel()

        self.bmm = EnergyModel(power_type=2)

        self.router = Router()
        # self.netDevices = {}
        self.sending_queue = []
        self.receiving_queue = []

        self.localtime = datetime(2021, 5, 7, 12, 0, 0)

        # self.forwardingTime = 0
        self.mobile.cal_pos(self)

    def reset(self):
        self.localtime = datetime(2021, 5, 7, 12, 0, 0)
        self.mobile.reset()
        self.mobile.cal_pos(self)
        self.sending_queue.clear()
        self.receiving_queue.clear()
        self.bmm.reset()

    def update_time(self, netTime):
        self.localtime = max(self.localtime, netTime)

    def update(self, time):
        self.mobile.cal_pos(self, time2list(time))
        self.bmm.decrease_device_energy()
        if self.mobile.in_sunlit:
            self.bmm.increase_energy()

    def send(self, event, nexthop):
        channel = self.net.edges[self.name, nexthop]['e']
        txtime = event.packet.size / channel.cal_rate()
        propdelay = channel.cal_prop_delay()
        event.packet.time += timedelta(seconds=txtime + propdelay)
        event.packet.delay += (txtime + propdelay)
        self.bmm.decrease_tx_energy(txtime)
        # event.packet.cur_node = nexthop
        return txtime, propdelay

    def receive(self, event):
        event.packet.time += event.duration
        event.packet.delay += event.duration.total_seconds()
        self.bmm.decrease_rx_energy(event.duration.total_seconds())

    def _ordered_candidates(self, packet):
        successors = list(self.net.successors(self.name))
        if not successors:
            return []

        preferred = self.router.look_up(packet)
        if preferred in successors:
            ordered = [preferred]
            for hop in successors:
                if hop != preferred:
                    ordered.append(hop)
            return ordered
        return successors

    def select_next_hop(self, packet):
        candidates = self._ordered_candidates(packet)
        if len(candidates) == 0:
            return None

        recent_nodes = set(packet.path_history[-self.net.runtime_config.tabu_backtrack_hops:])
        filtered = []

        for hop in candidates:
            if hop == packet.prev_node and len(candidates) > 1:
                self.net.metrics.record_loop_avoided()
                continue

            if packet.node_visit_count.get(hop, 0) >= self.net.runtime_config.max_visits_per_node:
                self.net.metrics.record_loop_avoided()
                continue

            if hop in recent_nodes and len(candidates) > 1:
                self.net.metrics.record_loop_avoided()
                continue

            filtered.append(hop)

        if len(filtered) > 0:
            return filtered[0]
        return candidates[0]

    def lookup(self, event):
        self.bmm.decrease_rtable_lookup(event.packet.size)
        event.packet.time += event.duration
        event.packet.delay += event.duration.total_seconds()
        event.packet.ttl -= 1

        # 1、到终点了
        if event.packet.d_node == self.name:
            event.packet.arrive = 1
            # return None
        # 2、ttl小于等于0，丢包了
        elif event.packet.ttl <= 0:
            event.packet.drop = 1
            event.packet.drop_reason = 'ttl_expired'
        else:
            event.packet.next_hop = self.select_next_hop(event.packet)
            # return None
        # 3、放到发送队列，准备发到下一跳
        # self.sending_queue.put(packet)
        # return nexthop

    def init_routing_table(self, successors, out_degrees):
        out_degree = out_degrees[self.name]
        for i in range(66):
            self.router.routing_table[f"{i+1}"] = successors[random.randint(0, out_degree-1)]

    def update_routing_table(self, actions):
        for k, v in actions.items():
            self.router.routing_table[k] = v
