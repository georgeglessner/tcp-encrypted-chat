# tcp-encrypted-chat

## Synopsis
Multiple clients are supported by one server and use RSA and Fernet's symmetric encryption to ensure secure chat communication.

## Commands
- Get a list of all clients:              `$clients`
- Broadcast a message to all clients:     `$broadcast [message]`
- Send a message to an individual client: `$sendto [username] [message]`
- Boot specific user: `$boot [username]`
  - will be prompted for an admin password
