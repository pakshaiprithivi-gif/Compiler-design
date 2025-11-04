"""
Consensus Algorithm Demonstrator (Paxos & Raft) - Single-file simulator

Usage:
    python paxos_raft_demo.py paxos   # runs a simple Paxos simulation
    python paxos_raft_demo.py raft    # runs a simple Raft simulation

This is an educational, in-process simulator (no real networking). It uses asyncio
and randomized timers to simulate message delivery and timing differences.

Notes:
- The Paxos implementation implements a simplified Multi-Paxos-like flow:
  proposers send prepare, accept requests to acceptors; learners learn chosen values.
- The Raft implementation includes leader election and simple log replication for commands.

This code is intentionally concise and readable for learning and demo purposes —
not production-grade.
"""

import asyncio
import random
import sys
import time
from collections import defaultdict, deque

# --------------------------- Utility / Network ---------------------------
class InProcessNetwork:
    """Simulate unreliable in-process message delivery with optional delay."""
    def __init__(self, drop_rate=0.0, delay_range=(0.01, 0.15)):
        self.drop_rate = drop_rate
        self.delay_range = delay_range
        self.queues = {}  # name -> asyncio.Queue

    def register(self, name):
        q = asyncio.Queue()
        self.queues[name] = q
        return q

    async def send(self, to, message):
        if random.random() < self.drop_rate:
            # drop message
            return
        await asyncio.sleep(random.uniform(*self.delay_range))
        if to in self.queues:
            await self.queues[to].put(message)

# --------------------------- Paxos Simulator ---------------------------
class PaxosAcceptor:
    def __init__(self, name):
        self.name = name
        self.promised_id = None
        self.accepted_id = None
        self.accepted_value = None

    async def on_prepare(self, proposal_id, proposer):
        # promise if proposal_id is higher than promised
        if self.promised_id is None or proposal_id > self.promised_id:
            self.promised_id = proposal_id
            return (True, self.accepted_id, self.accepted_value)
        return (False, self.accepted_id, self.accepted_value)

    async def on_accept_request(self, proposal_id, value):
        if self.promised_id is None or proposal_id >= self.promised_id:
            self.promised_id = proposal_id
            self.accepted_id = proposal_id
            self.accepted_value = value
            return True
        return False

class PaxosProposer:
    def __init__(self, name, acceptors, learners, network=None):
        self.name = name
        self.acceptors = acceptors
        self.learners = learners
        self.network = network
        self.proposal_seq = 0

    async def propose(self, value):
        self.proposal_seq += 1
        proposal_id = int(time.time()*1000) + self.proposal_seq
        # Phase 1: Prepare
        promises = []
        for a in self.acceptors:
            ok, acc_id, acc_val = await a.on_prepare(proposal_id, self.name)
            if ok:
                promises.append((acc_id, acc_val))
        # If majority promises
        if len(promises) <= len(self.acceptors)//2:
            print(f"[{self.name}] Prepare failed (no majority)")
            return False
        # Adopt highest-numbered previously-accepted value, if any
        highest = max((p for p in promises if p[0] is not None), default=(None, None))
        chosen_value = highest[1] if highest[1] is not None else value
        # Phase 2: Accept requests
        accepts = 0
        for a in self.acceptors:
            ok = await a.on_accept_request(proposal_id, chosen_value)
            if ok:
                accepts += 1
        if accepts > len(self.acceptors)//2:
            # notify learners
            for L in self.learners:
                L.learn(chosen_value)
            print(f"[{self.name}] Value chosen: {chosen_value}")
            return True
        else:
            print(f"[{self.name}] Accept failed (no majority)")
            return False

class PaxosLearner:
    def __init__(self, name):
        self.name = name
        self.learned = None

    def learn(self, value):
        self.learned = value
        print(f"[Learner {self.name}] Learned: {value}")

async def run_paxos_demo():
    print("--- Paxos Demo ---")
    # Create acceptors
    acceptors = [PaxosAcceptor(f'A{i}') for i in range(5)]
    learners = [PaxosLearner('L1')]
    # Two proposers race to propose different values
    p1 = PaxosProposer('P1', acceptors, learners)
    p2 = PaxosProposer('P2', acceptors, learners)

    # Schedule proposers with slight timing differences
    await asyncio.gather(
        asyncio.sleep(0.05),
        p1.propose('ReleaseWater'),
        asyncio.sleep(0.02),
        p2.propose('Evacuate'))

    print('\nFinal Learner state:')
    for L in learners:
        print(f' - {L.name}: {L.learned}')

# --------------------------- Raft Simulator ---------------------------
ROLE_FOLLOWER = 'follower'
ROLE_CANDIDATE = 'candidate'
ROLE_LEADER = 'leader'

class RaftNode:
    def __init__(self, name, peers, network=None, election_timeout=(0.15,0.35)):
        self.name = name
        self.peers = peers  # dict name->node (in-process)
        self.network = network
        self.current_term = 0
        self.voted_for = None
        self.log = []  # list of commands
        self.commit_index = -1
        self.last_applied = -1
        self.next_index = {}  # for leader
        self.match_index = {}
        self.role = ROLE_FOLLOWER
        self.votes_received = set()
        self.election_timeout = election_timeout
        self.election_task = None
        self.heartbeat_interval = 0.08
        self.stopped = False

    async def start(self):
        asyncio.create_task(self.run())

    async def run(self):
        while not self.stopped:
            if self.role == ROLE_FOLLOWER:
                # wait for timeout to become candidate
                await self.wait_for_election_timeout()
                print(f"[{self.name}] election timeout -> become candidate")
                await self.become_candidate()
            elif self.role == ROLE_CANDIDATE:
                await self.run_election()
            elif self.role == ROLE_LEADER:
                await self.send_heartbeats()
            await asyncio.sleep(0.01)

    async def wait_for_election_timeout(self):
        # simple randomized timeout
        await asyncio.sleep(random.uniform(*self.election_timeout))

    async def become_candidate(self):
        self.role = ROLE_CANDIDATE
        self.current_term += 1
        self.voted_for = self.name
        self.votes_received = {self.name}

    async def run_election(self):
        # request votes from peers
        print(f"[{self.name}] starting election for term {self.current_term}")
        for peer in self.peers.values():
            if peer.name == self.name: continue
            granted = await peer.on_request_vote(self.current_term, self.name)
            if granted:
                self.votes_received.add(peer.name)
        if len(self.votes_received) > len(self.peers)//2:
            print(f"[{self.name}] wins election, becomes leader (term {self.current_term})")
            await self.become_leader()
        else:
            # lost election -> back to follower
            self.role = ROLE_FOLLOWER

    async def on_request_vote(self, term, candidate_name):
        # grant vote if term >= current_term and haven't voted
        if term > self.current_term:
            self.current_term = term
            self.voted_for = None
            self.role = ROLE_FOLLOWER
        if (self.voted_for is None or self.voted_for == candidate_name) and term >= self.current_term:
            self.voted_for = candidate_name
            return True
        return False

    async def become_leader(self):
        self.role = ROLE_LEADER
        # initialize leader state
        for name in self.peers:
            self.next_index[name] = len(self.log)
            self.match_index[name] = -1

    async def send_heartbeats(self):
        # send empty AppendEntries as heartbeat
        for peer in self.peers.values():
            if peer.name == self.name: continue
            await peer.on_append_entries(self.current_term, self.name, [], self.commit_index)
        await asyncio.sleep(self.heartbeat_interval)

    async def on_append_entries(self, term, leader_name, entries, leader_commit):
        # accept leader
        if term >= self.current_term:
            self.current_term = term
            self.role = ROLE_FOLLOWER
            # append entries (simplified — no conflict handling)
            if entries:
                self.log.extend(entries)
            if leader_commit > self.commit_index:
                self.commit_index = min(leader_commit, len(self.log)-1)
            return True
        return False

    async def client_command(self, command):
        if self.role != ROLE_LEADER:
            print(f"[{self.name}] Not leader — redirecting to leader not implemented in demo")
            return False
        # append to log and replicate (simplified: synchronous replication to majority)
        self.log.append(command)
        self.match_index[self.name] = len(self.log)-1
        replicated = 1
        for peer in self.peers.values():
            if peer.name == self.name: continue
            ok = await peer.on_append_entries(self.current_term, self.name, [command], self.commit_index)
            if ok:
                replicated += 1
        if replicated > len(self.peers)//2:
            self.commit_index = len(self.log)-1
            print(f"[{self.name}] Command committed: {command}")
            return True
        else:
            print(f"[{self.name}] Command NOT committed: {command}")
            return False

async def run_raft_demo():
    print("--- Raft Demo ---")
    # create 5 nodes; peers reference each other
    nodes = {}
    for i in range(5):
        nodes[f'N{i}'] = RaftNode(f'N{i}', {})
    # wire peers
    for name,node in nodes.items():
        node.peers = nodes
    # start all nodes
    for node in nodes.values():
        asyncio.create_task(node.start())
    # let system run and stabilize
    await asyncio.sleep(1.0)
    # find leader
    leader = None
    for node in nodes.values():
        if node.role == ROLE_LEADER:
            leader = node
            break
    if leader is None:
        print('No leader elected in demo time')
        # wait a bit more
        await asyncio.sleep(1.0)
        for node in nodes.values():
            if node.role == ROLE_LEADER:
                leader = node
                break
    if leader:
        print(f'Leader is {leader.name}, sending client commands')
        await leader.client_command('SetMode=ALERT')
        await asyncio.sleep(0.2)
        await leader.client_command('ReleaseResources')
    else:
        print('Still no leader — increase demo time or tune timeouts')
    # show logs
    print('\nNode logs:')
    for node in nodes.values():
        print(f" - {node.name}: role={node.role}, term={node.current_term}, log={node.log}, commit_index={node.commit_index}")

# --------------------------- CLI ---------------------------

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python paxos_raft_demo.py [paxos|raft]')
        sys.exit(1)
    choice = sys.argv[1].lower()
    if choice == 'paxos':
        asyncio.run(run_paxos_demo())
    elif choice == 'raft':
        asyncio.run(run_raft_demo())
    else:
        print('Unknown choice. Use paxos or raft.')
