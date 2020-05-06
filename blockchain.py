import hashlib
import json
from urllib.parse import urlparse

from time import time
import requests


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)
    
    @property
    def last_block(self):
        # Returns the last block in the chain
        return self.chain[-1]

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid,

        Attributes:
            chain(list): A blockchain.

        Return(boolean):
            True if valid, False if not.
        
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print('\n---------------------\n')

            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

            return True

    def resolve_conflicts(self):
        """
        This is the Consensus Algorithm, it resolves conflicts by replacing
        the chain with the longest one in the networf.

        Return(boolean):
            True if the chain was replaced, False if not.
        
        """
        neighbours = self.nodes
        new_chain = None

        # Only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all nodes in the network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace the chain if a valid longer chain is discovered
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def register_node(self, address):
        """
        Add a new node to the list of nodes.

        Attributes:
            address(string): Address of node.

        Return(None).

        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def new_block(self, proof, previous_hash=None):
        """
        Creates a new block and add to the chain
        
        Attributes:
            proof(integer): The proof given by the Proof of Work algorithm.
            previous_hash(string): Optional hash of the previous block.

        Return(dict):
            A dict containing the block.

        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1])
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)

        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined block.

        Attributes:
            sender(string): Address of the sender.
            recipient(string): Adress of the recipient.
            amount(integer): Amount to be transfered.

        Return(integer):
            The index of the block that will hold this transaction.

        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a block.

        Attribute:
            block(dict): Block

        Return(string):
            A string with the hashed block.
        
        """
        # The dictionary must be sorted to avoid inconsistencies in the hashes
        block_string = json.dumps(block, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()

    def prof_of_work(self, last_proof):
        """
        Simple Proof of Work Algorithm.
        - Finds a number p' such that hash(pp') contains leading four zeroes, where p is the previous p'
        
        Attributes:
            last_proof(integer).
        
        Return(integer).

        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates the proof: Does hash(last_proof, proof) contain four leading zeroes?

        Attributes:
            last_proof(integer): Previous proof.
            proof(integer): Current proof.

        Return(boolean):
            True if correct, False if not.

        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == '0000'
