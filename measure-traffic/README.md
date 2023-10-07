
# usage

1. login mdx network gateway node
1. run `./sha256_hash.py`, which asks you to type a password twice; type the admin password of the network switches.  If the two passwords match, it saves the sha256 hash of the password into the file named `.passwd_hash`, with mode 0600. 
1. run `./get_traffic.py rnwl13 rnwl14 rnwl15 rnwl16 rnwl17 rnwl18`; it asks the password and check if it is correct by consulting the password hash file `.passwd_file` to measure the traffic and packet drops of these switches for 100 seconds.  results are saved into `data/` folder.
1. run `./visualize.py` reads `data/` and generate two graphviz files (up.dot and down.dot) along with their visualizations (up.pdf and down.pdf). PDF files are generated using dot tool, so you want to run it on a host that has it (you need only `data/` directory on the host you run this tool; the simplest is sshfs-mount the whole folder containing this tool and data)
