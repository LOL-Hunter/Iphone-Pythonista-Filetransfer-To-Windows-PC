from PIL import Image
import os
import appex
import ui, numpy as np
from console import input_alert, alert, hud_alert
from socket import socket, AF_INET, SOCK_STREAM
IP_ADDRESS = ''
PORT = 25565


class Client:
  def __init__(self):
    self.socket = socket(AF_INET, SOCK_STREAM)
    
  def connect(self):
    print(f'[STPC]: connecting to {IP_ADDRESS}:{PORT}')
    try:
      self.socket.settimeout(10)
      self.socket.connect((IP_ADDRESS, PORT))
      return True
    except Exception as e:
      alert('[STPC]', 'could not connect:'+str(e))
    
  def get(self):
    recv = str(self.socket.recv(1024), "utf8")
    if recv != '':
      return recv
        
  def send(self, msg):
    self.socket.send(bytes(msg, "utf8"))
  def sendB(self, msg):
    self.socket.send(msg)

  def close(self):
    self.socket.close()
    

def main():
  if not appex.is_running_extension():
    print('This script is intended to be run from the sharing extension.')
    return
  img = appex.get_image()
  if not img:
    alert('STPC', 'No input image! please select a valid image.')
    return
  conn = Client()
  if conn.connect():
    print('[STPC]: connection esablished!')
    if not img.mode.startswith('RGB'):
      img = img.convert('RGB')
    arr = np.array(img)
    file = open('data', 'wb')
    np.save(file, arr)
    file.close()
    print('[STPC]: Data successfully prepared!')
    print('[STPC]: Sending...')
    
    file = open('data', 'rb')
    ln= len(file.read())
    
    file.close()
    file = open('data', 'rb')
    
    
    conn.sendB(bytes(f'length:{ln}', 'utf8'))
    
    while True:
      if conn.get() is not None: break
    
    data = file.read(2048)
    conn.sendB(data)
  
    while data != b'':
      data = file.read(2048)
      conn.sendB(data)
    file.close()
    hud_alert('Data has been successfully transmitted.')
      
def checkConfig():
  global IP_ADDRESS
  if not os.path.exists('data.txt'):
    file = open('data.txt', 'w')
    file.close()
  file = open('data.txt')
  IP_ADDRESS=file.read()
  file.close()
  IP_ADDRESS = input_alert('IP-Adress from PC:','', IP_ADDRESS) 
  file = open('data.txt', 'w')
  file.write(IP_ADDRESS)
  file.close()
  
  
  
if __name__ == '__main__':
  checkConfig()
  main()
