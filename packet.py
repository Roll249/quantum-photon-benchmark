r'''
    base class for generating packages
'''


class Packet:
    size = 12000
    cid = 1

    def __init__(self, s_node, d_node, generateTime):
        super(Packet, self).__init__()
        self.s_node = s_node
        self.d_node = d_node
        self.cur_node = s_node
        self.drop = 0
        self.arrive = 0
        self.delay = 0
        self.ttl = 16
        self.time = generateTime
        self.econ = 0
        self.id = self.__class__.cid
        self.__class__.cid += 1
        self.prev_node = None
        self.path_history = [s_node]
        self.node_visit_count = {s_node: 1}
        self.send_retry_count = 0
        self.drop_reason = None
        self.next_hop = None

    def mark_visit(self, node_name):
        self.prev_node = self.cur_node
        self.cur_node = node_name
        self.path_history.append(node_name)
        self.node_visit_count[node_name] = self.node_visit_count.get(node_name, 0) + 1

    def is_expire(self):
        return self.ttl <= 0

    def __lt__(self, other):
        r"""
        主要定义在队列中的优先级（开始时间越小，优先级越高，如果开始时间相同，则比较结束时间）
        :param other: 其他的事件
        :return:
        """
        return self.time <= other.time
