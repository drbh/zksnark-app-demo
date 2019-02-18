from flask import request
from flask import Flask
from web3 import Web3
import subprocess
import json
import re
import sys
import signal
import docker

client = docker.from_env()


cfg = {
    "network": "http://127.0.0.1:7545",
    "contract_addr": "0x8125A1B0890F773760fC197A1C209616a633CbBA",
    "app_location": "/Users/drbh2/Desktop/zksnark-app-demo"
}

container = client.containers.run(
    "zokrates_tutorial",
    "sleep infinity",
    volumes={
        cfg["app_location"] + '/code': {
            'bind': '/home/zokrates/ZoKrates/target/debug/code',
            'mode': 'rw',
        }},
    detach=True)

cfg["docker_cont_name"] = container.name


def handler(signal, frame):
    container.kill()
    print('\n\n\nCONTAINER STOPPED')
    sys.exit(0)


print("Conneting to local Blockchain Network at %s" % cfg["network"])
w3 = Web3(Web3.HTTPProvider(cfg["network"]))


abi = [{
    "constant": False,
    "inputs": [
        {"name": "a", "type": "uint256[2]"}, {
            "name": "a_p", "type": "uint256[2]"},
        {"name": "b", "type": "uint256[2][2]"}, {
            "name": "b_p", "type": "uint256[2]"},
        {"name": "c", "type": "uint256[2]"}, {
            "name": "c_p", "type": "uint256[2]"},
        {"name": "h", "type": "uint256[2]"}, {
            "name": "k", "type": "uint256[2]"},
        {"name": "input", "type": "uint256[4]"}],
    "name": "verifyTx",
    "outputs": [{
            "name": "r",
            "type": "bool"
    }],
    "payable": False,
    "stateMutability": "nonpayable",
    "type": "function"
},
    {
        "anonymous": False,
        "inputs": [{
            "indexed": False,
            "name": "s",
            "type": "string"
        }],
        "name": "Verified",
        "type": "event"
}
]


contract = w3.eth.contract(
    abi=abi, address=cfg["contract_addr"])
c = contract.find_functions_by_name("verifyTx")[0]
print("Loaded in hashing smart contract at %s" %
      cfg["contract_addr"])


def flatten_proof(proof):
    inp = []
    for k, v in proof.items():
        if k == "proof":
            for key, val in v.items():
                if type(val[0]) != list:
                    entry = [int(vx, 16) for vx in val]
                else:
                    z = []
                    for vxt in val:
                        k = []
                        for vx in vxt:
                            k += [int(vx, 16)]
                        z += [k]
                    entry = z
                inp += [entry]
        else:
            inp += [proof["input"]]
    return inp


def compute_witness_docker(numerical_input, h0, h1):
    subprocess.call(
        "/usr/local/bin/docker exec -t " +
        cfg["docker_cont_name"] +
        " bash -c 'cd /home/zokrates/ZoKrates/target/debug/code/preimage/ && \
        /home/zokrates/zokrates compute-witness -a 0 0 0 " +
        numerical_input + " " + str(h0) + " " + str(h1) + "'", shell=True)

    with open(cfg["app_location"] +
              '/code/preimage/witness', 'r') as myfile:
        data = myfile.read().replace('\n', '')

    return data


def compute_get_hashes_witness_docker(numerical_input):
    subprocess.call(
        "/usr/local/bin/docker exec -t " +
        cfg["docker_cont_name"] +
        " bash -c 'cd /home/zokrates/ZoKrates/target/debug/code/get_hashes && \
        /home/zokrates/zokrates compute-witness -a 0 0 0 " + numerical_input + "'", shell=True)
    with open(cfg["app_location"] +
              '/code/get_hashes/witness', 'r') as myfile:
        data = myfile.read().replace('\n', '')
    return data


def generate_proof_docker():
    subprocess.call(
        "/usr/local/bin/docker  exec -t " +
        cfg["docker_cont_name"] +
        " bash -c 'cd /home/zokrates/ZoKrates/target/debug/code/preimage/ && \
        /home/zokrates/zokrates generate-proof'", shell=True)
    with open(cfg["app_location"]+'/code/preimage/proof.json') as f:
        data = json.load(f)
    return data


def witness_to_dict(data):
    nums = {}
    for z in data[0:90].split("~out_"):
        if z != "":
            y = z.split(" ")
            nums["h"+str(y[0])] = y[1]
    return nums


def verify_proof_eth(proof):
    inp = flatten_proof(proof)
    print(" ")
    print(json.dumps(inp, indent=4))
    try:
        response = c(*inp).call()
        print(response)
    except ValueError as e:
        print(e)
        response = False
    return response


def transact_proof_eth(proof):
    inp = flatten_proof(proof)
    response = c(*inp).transact({
        'from': "0x3C95586225e962249e58D010E838335C6EE8F930",
        'gas': (200*100*100)})
    return response.hex()


def create_witness_and_make_proof(input):
    witness_ref = compute_witness_docker(input)
    print("created witness")
    proof = generate_proof_docker()
    print("created proof")
    return proof


def start_docker():
    subprocess.call(
        "docker run -v $PWD/code:/home/zokrates/ZoKrates/target/debug/code \
        -ti zokrates_tutorial \/bin/bash", shell=True)


def build_deploy_zkp_contract():
    subprocess.call(
        ""+"truffle compile"+" && "+"truffle migrate", shell=True)


def hash_to_128(d): return [int(str(d)[0:34], 16), int(str(d)[34:], 16)]


app = Flask(__name__)


@app.route("/verify_local", methods=["POST"])
def verify_local():
    proof = json.loads(request.data)
    print(json.dumps(proof, indent=4))
    r = verify_proof_eth(proof)
    return json.dumps({"response": r})


@app.route("/verify", methods=["POST"])
def verify():
    proof = json.loads(request.data)
    print(json.dumps(proof, indent=4))
    r = transact_proof_eth(proof)
    return json.dumps({"response": r})


@app.route("/deploy")
def deploy():
    subprocess.call(
        "cd "+cfg["app_location"]+" && \
        truffle compile && truffle migrate", shell=True)
    return json.dumps({"status": 200})


@app.route("/proveit", methods=["POST"])
def proveit():
    payload = json.loads(request.data)
    h0, h1 = hash_to_128(payload["digest"])
    final_digest = hex(int(h0)) + hex(int(h1))[2:]
    print(final_digest, h0, h1, payload["preimage"])
    compute_witness_docker(payload["preimage"], h0, h1)
    proof = generate_proof_docker()
    return json.dumps(proof)


@app.route("/witness", methods=["POST"])
def witness():
    input = json.loads(request.data)["input"]
    witness_ref = compute_get_hashes_witness_docker(input)
    s = witness_ref[0:255]
    h1, h0 = re.search(
        r'1 .*~out', s).group()[2:-4], re.search(r'0 .*~one', s).group()[2:-4]
    final_digest = hex(int(h0)) + hex(int(h1))[2:]
    r = {
        "h0": h0,
        "h1": h1,
        "digest": final_digest
    }
    return json.dumps(r)


if __name__ == "__main__":
    app.run()
    print('\n\n\nPRESS CTRL-C AGAIN TO KILL DOCKER CONTAINER!')
    signal.signal(signal.SIGINT, handler)
    signal.pause()
