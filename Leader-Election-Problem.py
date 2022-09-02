import uuid
import json
import socket
from queue import Queue
import enum
import random
import time

## Create a enum class for node's status
class Node_Status(enum.Enum):
    non_participating = 1
    participating = 2
    decided = 3
    leader = 4
    offline = 5


##This function receive a json packet, parse it and return its values
def json_Parser(json_file):
    json_file_dict = json.loads(json_file)
    unique_ID = json_file_dict["source"]
    message_type = json_file_dict["type"]
    message_value = json_file_dict["value"]
    return unique_ID, message_type, message_value


##Creat class Node
class Node:

    ##Defining variables
    #Since the number of nodes should be at most 16-bit unsigned integer, the upper bound uses for generate random number is 65535 or 0xffff
    upper_bound = 0xffff 
    sender = socket.socket()
    receiver = socket.socket()

    ##Defining constructor
    def __init__(self):
        self.process()

    ##Defining process func
    def process(self):
        self.queue = Queue()
        self.node_status = Node_Status.non_participating
        self.elected_UID = 0
        #create a random node_id for each node
        self.node_id = random.randint(0, self.upper_bound)
        #Creat the initial json packet (election msg) and store it in the queue
        election_msg_dic = {
            "source": self.node_id,
            "type": "election-message",
            "value": self.node_id
        }
        election_msg = json.dumps(election_msg_dic)
        self.queue.put(election_msg)

    ##Preapre and send a Json packet if the queue is not empty
    def send(self):
        if (not self.queue.empty()):
            #Take msg from queue and parse it by calling json_Parser func
            popped_packet = self.queue.get()
            sender_unique_ID, message_type, message_value = json_Parser(
                popped_packet)
            #if msg = election, mark node as participating
            if (message_type == "election-message"):
                self.node_status = Node_Status.participating
                # call receive fnc of nodeObj to get the msg
            return popped_packet

        else:
            print("There is no packet in the queue")
            return False

    ##Receive func
    def receive(self, received_message, node_num):
        #parse the received json packet by calling json_Parser func
        sender_unique_ID, message_type, message_value = json_Parser(
            received_message)

        #compares the unique ID in the message with its own if msg = election
        if (message_type == "election-message"):
            print(
                f"Node {node_num} received an \"election-message\" type packet"
            )
            #If the UID in the election message is larger, the node remove all packets in its queue and store received msg
            if (sender_unique_ID > self.node_id):
                if (not self.queue.empty()):
                    self.queue.queue.clear()
                self.queue.put(received_message)
                return True

            #If the UID in the election message is smaller, and the process is not a participant, the node creates s packet with its UID and replace it in the queue
            elif ((sender_unique_ID < self.node_id)
                  and (self.node_status != Node_Status.participating)):
                new_election_message_dic = {
                    "source": self.node_id,
                    "type": message_type,
                    "value": message_value
                }
                new_election_message = json.dumps(new_election_message_dic)
                if (not self.queue.empty()):
                    self.queue.queue.clear()
                self.queue.put(new_election_message)
                return True

            #If the UID in the election message is smaller, and the process is a participant, discards the msg
            elif ((sender_unique_ID < self.node_id)
                  and (self.node_status == Node_Status.participating)):
                return True

            #If the sender's UID is the same as the UID of the node, create a new msg with type "elected" and new node-id
            elif (sender_unique_ID == self.node_id):
                self.node_status = Node_Status.leader
                elected_message_dic = {
                    "source": self.node_id,
                    "type": "elected",
                    "value": message_value
                }
                elected_message = json.dumps(elected_message_dic)
                if (not self.queue.empty()):
                    self.queue.queue.clear()
                self.queue.put(elected_message)
                print(
                    f"node {node_num} changes the message type to \"elected\", since it received a packet with the same UID as itself"
                )
                return True

        #when a non-leader node receives an "elected" msg, marks itself as "elected" and store the msg in its queue
        elif ((message_type == "elected")
              and (self.node_status != Node_Status.leader)):
            self.node_status = Node_Status.decided
            self.elected_UID = sender_unique_ID
            if (not self.queue.empty()):
                self.queue.queue.clear()
            print(f"node {node_num} received an \"elected\" type packet")
            self.queue.put(received_message)
            return True

        #if a leader node receive an elected type msg, it broa the game is over
        elif ((message_type == "elected")
              and (self.node_status == Node_Status.leader)):
            print(f"\nNode {node_num} received an \"elected\" type packet")
            print(f"Node {node_num} is a \"leader\" node")
            print(
                f"So node {node_num} with UID {self.node_id} is the leader \n\nGame is over"
            )
            return False


##Define the main func
def main():
    ##Defining variables
    nodes = []
    run_loop = True
    delays = []

    ## read the number of nodes in the network
    while True:
        num_of_nodes = input("Please enter the number of nodes: ")
        try:
            n = int(num_of_nodes)
            if n <= 0:
                raise NotPositiveError
            break
        except ValueError:
            print("This was not a number, please try again")
        except:
            print("The number was not positive, please try again")
    print(f'\nNumber of nodes is: {n}\n')

    ## Define n instances of class Node
    for i in range(n):
        node = Node()
        nodes.append(node)
        print(f"node id for node {i} is: {nodes[i].node_id}")
    print("\n")

    ## read the delays between the nodes
    for i in range(n):
        while True:
            delay = input(
                f"Please enter the delay between node {i} and node {((i+1) % n)}: "
            )
            try:
                delay = float(delay)
                if delay <= 0:
                    raise NotPositiveError
                break
            except ValueError:
                print("This was not a number, please try again")
            except:
                print("The number was not positive, please try again")
        delays.append(delay)

    print(f'\nThe delay list is: {delays}\n')

    ##To simplify the program, the user specify the starter node
    while True:
        starter_node = input(
            f"Please indicate which node should initiate the game. The entered value must be between {0} and {n-1}: "
        )
        try:
            starter_node = int(starter_node)
            if ((starter_node < 0) or (starter_node > n-1)):
                raise NotPositiveError
            break
        except ValueError:
            print("This was not a number, please try again")
        except:
            print("The number was not valid, please try again")

    print(f'\nNode {starter_node} is starting the game\n')
    time.sleep(1)

    #assign unknown port numbers t each node, in case we want to use socket
    #port_numbers = []
    #for i in range (n):
    #  port_num = 9000 + i
    #  port_numbers.append(port_num)
    #  print(f"Port number for node {i} is {port_numbers[i]}')
    #print("\n")

    ##Start sending packet and find the leader
    while (run_loop):
        for node_num in range(starter_node, n):
            pkt = nodes[node_num].send()
            print(
                f"Node {node_num} is sending a packet to node {((node_num+1) % n)}."
            )
            print(
                f"Delay time between node {node_num} and {((node_num+1) % n)} is: {delays[node_num]} \n"
            )
            time.sleep(delays[node_num])
            run_loop = nodes[((node_num + 1) % n)].receive(
                pkt, ((node_num + 1) % n))
            if (not run_loop):
                break
        starter_node = 0


if __name__ == "__main__":
    main()
