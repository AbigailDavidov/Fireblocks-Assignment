# Fireblocks Assignment- Using API to transfer assets from wallet with balance threshold
In this project, I'm using Fireblocks to transfer assets between wallets, monitoring the transactions through code.<br>
I used fireblocks documentation to connect, and use their API and Webhooks.<br>
https://developers.fireblocks.com/reference/api-overview<br>
https://developers.fireblocks.com/docs/webhooks-notifications<br>
I used Flask to run my app, initiate transactions and listen to transaction notifications.<br>
In order to run my code you can clone this project, go to the location of the project in your terminal and simply run:<br>
```
pip install -r requirements. txt
```
Then you need to get the config and secret key files from me:)<br>
I'm thinking of a way to run this on AWS maybe using lambda, <br>
The idea is to create a server in EC2 that listens to traffic from a port, and use Lambda to send HTTP requests to the EC2 server.<br>
