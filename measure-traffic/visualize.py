#!/usr/bin/python3
import glob
import re
import os

DBG = 1

esxi_to_vm_name = {
    "gx031" : "node00",
    "gx020" : "node01",
    "gx011" : "node02",
    "gx015" : "node03",
    "gx017" : "node04",
    "gx021" : "node05",
    "gx024" : "node06",
    "gx032" : "node07",
    "gx001" : "node08",
    "gx006" : "node09",
    "gx014" : "node10",
    "gx022" : "node11",
    "gx002" : "node12",
    "gx016" : "node13",
    "gx025" : "node14",
    "gx009" : "node15",
}
    

class data_parser:
    def __init__(self, filename):
        self.filename = filename
        self.fp = open(filename)
        self.line_no = 0
        self.eof = 0
        self.next()

    def end(self):
        self.fp.close()
        self.fp = None
        
    def token_kind(self, line_no, line):
        for kind, pat in self.patterns:
            m = pat.match(line)
            if m:
                return kind, m
        assert(0), (line_no, line)
        
    def next(self):
        assert(self.eof == 0), self.eof
        try:
            self.line = next(self.fp)
        except StopIteration:
            self.line = ""
            self.eof = 1
        self.line_no += 1
        self.kind, self.m = self.token_kind(self.line_no, self.line)
        return self.kind

    def eat(self, kind, D):
        assert(self.kind == kind), (self.filename, self.line_no, self.kind, kind)
        D.update(self.m.groupdict())
        self.next()
        return D

TOK_IFCONFIG_DATE       = "TOK_IFCONFIG_DATE"
TOK_IFCONFIG_IF_BEGIN   = "TOK_IFCONFIG_IF_BEGIN"
TOK_IFCONFIG_IF_END     = "TOK_IFCONFIG_IF_END"
TOK_IFCONFIG_RX_PACKETS = "TOK_IFCONFIG_RX_PACKETS"
TOK_IFCONFIG_RX_ERRORS  = "TOK_IFCONFIG_RX_ERRORS"
TOK_IFCONFIG_TX_PACKETS = "TOK_IFCONFIG_TX_PACKETS"
TOK_IFCONFIG_TX_ERRORS  = "TOK_IFCONFIG_TX_ERRORS"
TOK_IFCONFIG_MISC       = "TOK_IFCONFIG_MISC"

class ifconfig_data_parser(data_parser):
    def __init__(self, filename):
        self.patterns = [
            (TOK_IFCONFIG_DATE,
             re.compile("=== (?P<y>\d+)\-(?P<m>\d+)\-(?P<d>\d+)\-(?P<H>\d+):(?P<M>\d+):(?P<S>\d+) ===")),
            (TOK_IFCONFIG_IF_BEGIN,
             re.compile("(?P<iface>[A-Za-z0-9_\.\-]+): flags=")),
            (TOK_IFCONFIG_IF_END,
             re.compile("^$")),
            (TOK_IFCONFIG_RX_PACKETS,
             re.compile(" +RX packets (?P<rx_packets>\d+) +bytes (?P<rx_bytes>\d+)")),
            (TOK_IFCONFIG_RX_ERRORS,
             re.compile(" +RX errors (?P<rx_errors>\d+) +dropped (?P<rx_dropped>\d+) +overruns (?P<rx_overruns>\d+) +frame (?P<rx_frame>\d+)")),
            (TOK_IFCONFIG_TX_PACKETS,
             re.compile(" +TX packets (?P<tx_packets>\d+) +bytes (?P<tx_bytes>\d+)")),
            (TOK_IFCONFIG_TX_ERRORS,
             re.compile(" +TX errors (?P<tx_errors>\d+) +dropped (?P<tx_dropped>\d+) +overruns (?P<tx_overruns>\d+) +carrier (?P<tx_carrier>\d+) +collisions (?P<tx_collisions>\d+)")),
            (TOK_IFCONFIG_MISC,
             re.compile(" +[A-Za-z]+")),
        ]
        super().__init__(filename)

    def ifconfig_if(self):
        D = {}
        self.eat(TOK_IFCONFIG_IF_BEGIN, D)
        while self.kind == TOK_IFCONFIG_MISC:
            self.eat(TOK_IFCONFIG_MISC, D)
        self.eat(TOK_IFCONFIG_RX_PACKETS, D)
        self.eat(TOK_IFCONFIG_RX_ERRORS, D)
        self.eat(TOK_IFCONFIG_TX_PACKETS, D)
        self.eat(TOK_IFCONFIG_TX_ERRORS, D)
        while self.kind == TOK_IFCONFIG_MISC:
            self.eat(TOK_IFCONFIG_MISC, D)
        self.eat(TOK_IFCONFIG_IF_END, D)
        return D

    def date(self):
        return self.eat(TOK_IFCONFIG_DATE, {})

    def ifconfig_data(self):
        self.stats = []
        self.begin_date = self.date()
        if DBG>=2:
            print(f"begin_date: {self.begin_date}")
        while self.kind == TOK_IFCONFIG_IF_BEGIN:
            intf = self.ifconfig_if()
            self.stats.append(intf)
            if DBG>=3:
                print(f"intf: {intf}")            
        self.end_date = self.date()
        if DBG>=2:
            print(f"end_date: {self.end_date}")
        self.end()

TOK_BWM_DATE   = "TOK_BWM_DATE"
TOK_BWM_RECORD = "TOK_BWM_RECORD"
TOK_BWM_EOF    = "TOK_BWM_EOF"

class bwm_data_parser(data_parser):
    def __init__(self, filename):
        self.patterns = [
            (TOK_BWM_DATE,
             re.compile("=== (?P<y>\d+)\-(?P<m>\d+)\-(?P<d>\d+)\-(?P<H>\d+):(?P<M>\d+):(?P<S>\d+) ===")),
            (TOK_BWM_RECORD,
             # man bwm-ng
             # unix timestamp;iface_name;bytes_out/s;bytes_in/s;bytes_total/s;bytes_in;bytes_out;packets_out/s;packets_in/s;packets_total/s;packets_in;packets_out;errors_out/s;errors_in/s;errors_in;errors_out
             re.compile("(?P<timestamp>\d+);"
                        "(?P<iface>[A-Za-z0-9_\.\-]+);"
                        "(?P<bytes_out_s>\d+(\.\d+)?);"
                        "(?P<bytes_in_s>\d+(\.\d+)?);"
                        "(?P<bytes_total_s>\d+(\.\d+)?);"
                        "(?P<bytes_in>\d+(\.\d+)?);"
                        "(?P<bytes_out>\d+(\.\d+)?);"
                        "(?P<packets_out_s>\d+(\.\d+)?);"
                        "(?P<packets_in_s>\d+(\.\d+)?);"
                        "(?P<packets_total_s>\d+(\.\d+)?);"
                        "(?P<packets_in>\d+(\.\d+)?);"
                        "(?P<packets_out>\d+(\.\d+)?);"
                        "(?P<errors_out_s>\d+(\.\d+)?);"
                        "(?P<errors_in_s>\d+(\.\d+)?);"
                        "(?P<errors_in>\d+(\.\d+)?);"
                        "(?P<errors_out>\d+(\.\d+)?)")),
            (TOK_BWM_EOF,
             re.compile("^$")),
            
        ]
        super().__init__(filename)

    def date(self):
        return self.eat(TOK_BWM_DATE, {})

    def bwm_record(self):
        return self.eat(TOK_BWM_RECORD, {})

    def bwm_data(self):
        self.stats = []
        self.begin_date = self.date()
        if DBG>=2:
            print(f"begin_date: {self.begin_date}")
        while self.kind == TOK_BWM_RECORD:
            rec = self.bwm_record()
            self.stats.append(rec)
            if DBG>=3:
                print(f"rec: {rec}")
        self.end_date = self.date()
        if DBG>=2:
            print(f"end_date: {self.end_date}")
        self.end()

TOK_INTERFACE_RECORD = "TOK_INTERFACE_RECORD"
TOK_INTERFACE_END    = "TOK_INTERFACE_END"

class interface_data_parser(data_parser):
    def __init__(self, filename):
        self.patterns = [
            (TOK_INTERFACE_RECORD,
             re.compile("(?P<state>[A-Za-z0-9_\-\/]+) +"
                        "(?P<name>[A-Za-z0-9_\.\-\/]+) +"
                        "(?P<mode>[A-Za-z0-9_\.\-\/]+) *"
                        "(?P<alias>.*)")),
            (TOK_INTERFACE_END,
             re.compile("^$")),
        ]
        super().__init__(filename)
        
    def interface(self):
        return self.eat(TOK_INTERFACE_RECORD, {})
        
    def interface_data(self):
        self.interfaces = []
        # skip first two lines
        self.eat(TOK_INTERFACE_RECORD, {})
        self.eat(TOK_INTERFACE_RECORD, {})
        while self.kind == TOK_INTERFACE_RECORD:
            self.interfaces.append(self.interface())
        self.eat(TOK_INTERFACE_END, {})
        self.end()
            
def read_data():
    interfaces = []
    ifconfig_stats = []
    bw_stats = []
    for interface_txt in glob.glob("data/*_interface.txt"):
        p = interface_data_parser(interface_txt)
        p.interface_data()
        interfaces.append((interface_txt, p.interfaces))
    for ifconfig_txt in glob.glob("data/*_ifconfig.txt"):
        p = ifconfig_data_parser(ifconfig_txt)
        p.ifconfig_data()
        ifconfig_stats.append((ifconfig_txt, p.stats))
    for bw_txt in glob.glob("data/*_bw.txt"):
        p = bwm_data_parser(bw_txt)
        p.bwm_data()
        bw_stats.append((bw_txt, p.stats))
    return (ifconfig_stats, bw_stats, interfaces)

def get_host_from_filename(filename):
    m = re.search("(?P<host>[A-Za-z0-9_\-]+)_[a-z]+.txt", filename)
    return m.group("host")

def get_host_from_alias(alias):
    # R11_gx031-r2 -> gx031
    m = re.match("R\d\d_(?P<host>[A-Za-z0-9]+)\-r\d", alias)
    if m:
        return m.group("host")
    else:
        return None

def get_other_host(aliases, host, iface):
    alias = aliases[host].get(iface, "")
    the_other_host = get_host_from_alias(alias)
    if the_other_host is None:
        the_other_host = iface
    return the_other_host
        
def high_bytes(bw_stats, aliases):
    bytes_data = {}           # bytes_out_data[a][b] = [ x0, x1, ... ]
    for filename, stats in bw_stats:
        host = get_host_from_filename(filename) # rnwl14 etc.
        bytes_data[host] = {}
        for s in stats:
            iface = s["iface"]
            if iface == "total":
                continue
            bytes_out = int(s["bytes_out"])
            bytes_in = int(s["bytes_in"])
            if iface not in bytes_data[host]:
                bytes_data[host][iface] = {"out" : [], "in" : []}
            bytes_data[host][iface]["out"].append(bytes_out)
            bytes_data[host][iface]["in"].append(bytes_in)
    traffic = {}
    for host in bytes_data:
        for iface in bytes_data[host]:
            o = sum(bytes_data[host][iface]["out"])
            i = sum(bytes_data[host][iface]["in"])
            the_other_host = get_other_host(aliases, host, iface)
            if DBG>=2:
                print(f"{host} -> {iface} ({the_other_host}) out={o}, in={i}")
            if (host,the_other_host) not in traffic:
                traffic[host,the_other_host] = 0
            traffic[host,the_other_host] += o
            if (the_other_host,host) not in traffic:
                traffic[the_other_host,host] = 0
            traffic[the_other_host,host] += i
    return traffic

def high_dropped(ifconfig_stats, aliases):
    dropped_data = {}
    for filename, stats in ifconfig_stats:
        host = get_host_from_filename(filename) # rnwl14 etc.
        # dropped_data[host][iface]["tx"/"rx"] = [x0, x1, ... ]
        dropped_data[host] = {}
        for s in stats:
            iface = s["iface"]
            if iface not in dropped_data[host]:
                dropped_data[host][iface] = {"tx" : [], "rx" : []}
            dropped_data[host][iface]["rx"].append(int(s["rx_dropped"]))
            dropped_data[host][iface]["tx"].append(int(s["tx_dropped"]))
    dropped = {}
    for host in dropped_data:
        for iface in dropped_data[host]:
            rx = dropped_data[host][iface]["rx"][-1] - dropped_data[host][iface]["rx"][0]
            tx = dropped_data[host][iface]["tx"][-1] - dropped_data[host][iface]["tx"][0]
            the_other_host = get_other_host(aliases, host, iface)
            if DBG>=2:
                print(f"{host} -> {iface} ({the_other_host}) rx={rx}, tx={tx}")
            if (host,the_other_host) not in dropped:
                dropped[host,the_other_host] = 0
            dropped[host,the_other_host] += tx
            if (the_other_host,host) not in dropped:
                dropped[the_other_host,host] = 0
            dropped[the_other_host,host] += rx
    return dropped

def make_alias_table(interfaces):
    aliases = {}                # alias[host][iface] = alias
    for filename, interfaces_of_host in interfaces:
        host = get_host_from_filename(filename) # rnwl14 etc.
        aliases[host] = {}
        for s in interfaces_of_host:
            iface = s["name"]
            alias = s["alias"]
            aliases[host][iface] = alias
    return aliases

TRAFFIC_THRESHOLD = 1e9        # >30GB
DROP_THRESHOLD = 10

def node_layer(node):
    if node[:1] == "s":
        return 2
    if node[:1] == "r":
        return 1
    return 0
    
def save_graph(traffic, dropped, direction, filename):
    # list all nodes ever involved in high traffic or drop
    nodes = set([])
    for (s, d), tr in traffic.items():
        if tr > TRAFFIC_THRESHOLD:
            nodes.add(s)
            nodes.add(d)
    with open(filename, "w") as wp:
        wp.write("digraph G {\n")
        for (s, d), tr in sorted(traffic.items()):
            if s in nodes and d in nodes and (node_layer(d) - node_layer(s)) * direction > 0:
                tr_int = int(tr * 1e-9)
                dr = dropped.get((s, d), 0)
                if tr > TRAFFIC_THRESHOLD or dr > DROP_THRESHOLD:
                    label = f' [label="{tr_int}GB\n{dr}"]'
                    s_vm = esxi_to_vm_name.get(s)
                    d_vm = esxi_to_vm_name.get(d)
                    if s_vm is not None:
                        s = f"{s}\n{s_vm}"
                    if d_vm is not None:
                        d = f"{d}\n{d_vm}"
                    wp.write(f' "{s}" -> "{d}"{label};\n')
        wp.write("}\n")

def main():
    ifconfig_stats, bw_stats, interfaces = read_data()
    aliases = make_alias_table(interfaces)
    traffic = high_bytes(bw_stats, aliases)
    dropped = high_dropped(ifconfig_stats, aliases)
    save_graph(traffic, dropped, 1, "data/up.dot")
    save_graph(traffic, dropped, -1, "data/down.dot")
    os.system("dot data/up.dot -Tpdf -o data/up.pdf")
    os.system("dot data/down.dot -Tpdf -o data/down.pdf")
    print("OK")
    # return bytes_out, bytes_in, rx_dropped, tx_dropped
    return 0

main()
