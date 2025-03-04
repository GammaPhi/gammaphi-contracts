const Lamden = require('lamden-js')
const fs = require('fs')
require('dotenv').config()

const senderSk = process.env.LAMDEN_SK
const senderVk = process.env.LAMDEN_VK
const sendTo = process.env.SEND_TO
const sendAmount = parseInt(process.env.SEND_AMOUNT || '100', 10)
const maxStamps = 100

let networkInfo = (process.env.NETWORK === 'mainnet') ? {
    // Optional: Name of network
    name: 'Lamden Public Mainnet',
    // Required: type of network 'mockchain', 'testnet', 'mainnet'
    type: 'mainnet',
    // Required: must begin with http or https
    hosts: ["https://masternode-01.lamden.io:443"]
} : {
    // Optional: Name of network
    name: 'Lamden Public Testnet',
    // Required: type of network 'mockchain', 'testnet', 'mainnet'
    type: 'testnet',
    // Required: must begin with http or https
    hosts: ['https://testnet-master-1.lamden.io'],
}

console.log(networkInfo)

const kwargs = {
    amount: sendAmount,
    to: sendTo,
}

const txInfo = {
    senderVk,
    contractName: "currency",
    methodName: "transfer",
    kwargs,
    stampLimit: maxStamps, //Max stamps to be used. Could use less, won't use more.
}

console.log(txInfo);

let tx = new Lamden.TransactionBuilder(networkInfo, txInfo)

tx.getNonce((res, err) => {
    if (err) {
        console.log("Nonce Not Set")
        return
    }
    tx.events.on('response', (response) => {
        console.log(response)
        if (tx.resultInfo.type === 'error') return
        console.log("Success!")
    })
    tx.send(senderSk).then(() => tx.checkForTransactionResult())
    console.log(res)
})



