# zksnark-app-demo
A zksnark application demo that test zero knowledge proofs and smart contract verification

#### Install
```
git clone https://github.com/drbh/zksnark-app-demo.git
cd zksnark-app-demo/
```

#### Configure
First open up the `app.py` file and edit the `cfg` object to reflect the directory you have the files in

You will likely only need to change `app_location` since Ganache runs at `http://127.0.0.1:7545` on default, and `0x8125A1B0890F773760fC197A1C209616a633CbBA` seems to be the default address for the second deployed smart contract
```
cfg = {
    "network": "http://127.0.0.1:7545",
    "contract_addr": "0x8125A1B0890F773760fC197A1C209616a633CbBA",
    "app_location": "/Users/drbh2/Desktop/zksnark-app-demo"
}
```

#### Run App
Okay, no we just need to start the server up

```
python3 app.py
```

and we should see the following... 

```
Conneting to local Blockchain Network at http://127.0.0.1:7545
Loaded in hashing smart contract at 0x8125A1B0890F773760fC197A1C209616a633CbBA
 * Serving Flask app "app" (lazy loading)
 * Environment: production
   WARNING: Do not use the development server in a production environment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

#### Directory Structure

```
├── app.py
├── code
│   ├── get_hashes
│   │   ├── hash.code
│   │   ├── out
│   │   ├── out.code
│   │   └── witness
│   └── preimage
│       ├── hashexample.code
│       ├── my.patch
│       ├── out
│       ├── out.code
│       ├── proof.json
│       ├── proving.key
│       ├── variables.inf
│       ├── verification.key
│       ├── verifier.sol
│       └── witness
├── contracts
│   ├── Migrations.sol
│   └── Verifier.sol
├── migrations
│   ├── 1_initial_migration.js
│   └── 2_deploy_contracts.js
├── package-lock.json
├── test
└── truffle-config.js

6 directories, 21 files
```
