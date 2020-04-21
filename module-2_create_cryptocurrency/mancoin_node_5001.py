# Module 2 create a CryptoCurrency
# To be install
# Flex = 0.12.2 pip install Flask==0.12.2
#pip install -U Flask
# PostMan http client
# requests==2.18.4 pip install requests==2.18.4
# importing the library
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse


# part 1 Building a bitcoin
class Blockchain:
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, previous_hash='0')
        self.nodes = set()

    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions}
        self.transactions = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while not check_proof:
            hash_operation = hashlib.sha256(str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] == "0000":
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_transactions(self, sender, receiver, amount):
        self.transactions.append({'sender': sender,
                                  'receiver': receiver,
                                  'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_nodes(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for nodes in network:
            response = requests.get(f'http://{nodes}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False


# part 2 mining our blockChain

# Creating web app
app = Flask(__name__)
# Creating address for the node on port 5000
node_address = str(uuid4()).replace('-', '')

# creating a blockchain
blockchain = Blockchain()


# Mining a new block

@app.route('/', methods=['GET'])
def hello():
    return "Hello", 200


@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transactions(sender=node_address, receiver='You5001', amount=1)
    block = blockchain.create_block(proof, previous_hash)
    response = {
        'message': 'Done',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': block['transactions']
    }
    return jsonify(response), 200


@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


@app.route('/is_valid_chain', methods=['GET'])
def is_valid_chain():
    return str(blockchain.is_chain_valid(blockchain.chain)), 200


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return " Key Missing ", 400
    index = blockchain.add_transactions(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'This transaction added {index}'}
    return jsonify(response), 201


@app.route('/connect_nodes', methods=['POST'])
def connect_nodes():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No Node", 400
    for node in nodes:
        blockchain.add_nodes(node)
    response = {'message': ' All the node are now connected',
                'total_nodes': list(blockchain.nodes)
                }
    return jsonify(response)


@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replace = blockchain.replace_chain()
    if is_chain_replace:
        response = {
            'message': 'Chain Replaced',
            'chain': blockchain.chain
        }
    else:
        response = {
            'message': 'All Good',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


# Part 3 decentralizing our blockChain


# Running app
app.run('0.0.0.0', port=5001, debug=True)
app.debug = True
#app.run(debug=True)
