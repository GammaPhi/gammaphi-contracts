const Lamden = require('lamden-js')
const fs = require('fs')
require('dotenv').config()

const senderSk = process.env.LAMDEN_SK
const senderVk = process.env.LAMDEN_VK
const contractPath = process.env.CONTRACT_PATH
const owner = process.env.OWNER || null
const name = process.env.NAME
const maxStamps = parseInt(process.env.MAX_STAMPS || '1000', 10)

console.log(process.env)

let networkInfo = (process.env.NETWORK === 'mainnet') ? {
    // Optional: Name of network
    name: 'Lamden Public Mainnet',
    // Required: type of network 'mockchain', 'testnet', 'mainnet'
    type: 'mainnet',
    // Required: must begin with http or https
    hosts: ["https://masternode-01.lamden.io:443"],
    //blockservice_hosts: ['https://blocks.gammaphi.io']
} : {
    // Optional: Name of network
    name: 'Lamden Public Testnet',
    // Required: type of network 'mockchain', 'testnet', 'mainnet'
    type: 'testnet',
    // Required: must begin with http or https
    hosts: ['https://testnet-master-1.lamden.io'],
}

console.log(networkInfo)

const code = fs.readFileSync(contractPath).toString('utf-8');

const kwargs = {
    code: code,
    name: name,
}
if (owner !== null) {
    kwargs.owner = owner
}

const txInfo = {
    senderVk,
    contractName: "submission",
    methodName: "submit_contract",
    kwargs,
    //nonce: 104,
    //processor: '5b09493df6c18d17cc883ebce54fcb1f5afbd507533417fe32c006009a9c3c4a',
    stampLimit: maxStamps, //Max stamps to be used. Could use less, won't use more.
}

console.log(txInfo);

let tx = new Lamden.TransactionBuilder(networkInfo, txInfo)

tx.events.on('response', (response) => {
    console.log(response)
    if (tx.resultInfo.type === 'error') return
    console.log("Success!")
})
tx.send(senderSk).then(() => tx.checkForTransactionResult())


/*tx.getNonce((res, err) => {
    if (err) {
        console.log("Nonce Not Set")
        return
    }
    console.log(res)

})*/



