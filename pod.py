# cython: language=c++
# coding: utf-8
import serial.tools.list_ports
import os
import pyaudio
import sounddevice as sd
from piper.voice import PiperVoice
import multiprocessing as mp
from multiprocessing import Pool, Process, Value, Lock
import torch #install according to https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048 and run sudo apt-get install libopenblas-base libopenmpi-dev libomp-dev
import subprocess
import pyzed.sl as sl
import numpy as np
import cv2
import sys
import pandas
from plumbum import SshMachine
import socket
import secrets
import mysql.connector as mariadb
from mysql.connector import pooling
import calendar
import sys
import geocoder
import pandas as pd
import datetime
import time
#from ultralytics import YOLOv10
from ultralytics import YOLO
import evdev
from evdev import InputDevice, categorize, ecodes
from datetime import datetime
import serial
import time
import struct
import signal
import sys
import xml.etree.ElementTree as ET
import logging
from evdev import InputDevice, categorize, ecodes
import pygame
import select

def datalogic(shared_dict):
  print ("********************* STARTING DATALOGIC PROCESS *************************")
  os.nice(0) 
  print(f"Running process datalogic with niceness: {os.nice(0)} and pid {os.getpid()}")
  # Function to find the NFC reader device
  def find_barcode_reader():
    print ("Looking for barcode reader")
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
      print(f'Checking device: {device.path} - {device.name}')
      if 'Datalogic' in device.name:
        print ("Found barcode scanner with name: ", device)
        return device
    return None
  
  # Find the barcode reader device
  device = find_barcode_reader()
  if not device:
    print("Barcode reader not found. Exiting")
    exit()
  else:
    print(f'Reading from device: {device}')
    
  key_map = {'KEY_0': '0', 'KEY_1': '1', 'KEY_2': '2', 'KEY_3': '3', 'KEY_4': '4','KEY_5': '5', 'KEY_6': '6', 'KEY_7': '7', 'KEY_8': '8', 'KEY_9': '9'}
  while True:
      barcode = ""
      for event in device.read_loop():
        if event.type == ecodes.EV_KEY:
          key_event = categorize(event)
          if key_event.keystate == key_event.key_down:
            key_char = key_map.get(key_event.keycode, '')
            if key_char:
              barcode += key_char

        if event.type == ecodes.EV_KEY and event.code == ecodes.KEY_ENTER and event.value == 1:
          if barcode!="":
            if shared_dict['moveto'] ==0:
              shared_dict['barcode'] = str(barcode)
              shared_dict['method'] = "b"
              shared_dict['label']="product"
              print(f'barcode: {barcode}')
              if barcode!="5017007603276": 
                shared_dict['moveto'] = 1
              else:
                shared_dict['moveto'] = 2
              print("Setting to ",shared_dict['moveto'])
              barcode = ""

def zed(shared_dict):
  print ("********************* STARTING ZED PROCESS *************************")
  os.nice(0) 
  print(f"Running process zed with niceness: {os.nice(0)} and pid {os.getpid()}")
  #model = YOLOv10('/root/yolov10/weights/yolov10m.pt')
  #model1 = YOLO("yolo11m.pt")
  #model1.export(format="engine", device="dla:1", half=True) 
  #model = YOLO("yolo11n.engine")
  model = YOLO("yolo11m.pt")
  model.cuda()  # GPU
  model.to(torch.device(0))
  # Create a ZED Camera object
  zed = sl.Camera()
  # Set configuration parameters
  init_params = sl.InitParameters()
  init_params.camera_resolution = sl.RESOLUTION.HD720  # Use HD720 video mode
  init_params.coordinate_units = sl.UNIT.MILLIMETER     # Set units to millimeters
  # Open the camera
  if zed.open(init_params) != sl.ERROR_CODE.SUCCESS:
    print("Error opening ZED camera")
    zed.close()
    exit(1)
  while True:
    # Create Mats to store images
    image_left = sl.Mat()
    image_right = sl.Mat()
    input_size = (640, 640)  # YOLOv8 default input size, adjust if needed
    # Capture one frame
    if zed.grab() == sl.ERROR_CODE.SUCCESS:
        # Retrieve left and right images
        zed.retrieve_image(image_left, sl.VIEW.LEFT)
        zed.retrieve_image(image_right, sl.VIEW.RIGHT)

        # Convert sl.Mat to numpy array
        left_image_np = image_left.get_data()
        left_image_rgb = cv2.cvtColor(left_image_np, cv2.COLOR_BGRA2BGR)

        right_image_np = image_right.get_data()
        right_image_rgb = cv2.cvtColor(right_image_np, cv2.COLOR_BGRA2BGR)

        left_image_resized = cv2.resize(left_image_rgb, input_size)
        right_image_resized = cv2.resize(right_image_rgb, input_size)

        # Run YOLO model inference on both images
        
        resultsleft = model.track(left_image_resized, verbose=False, persist=True)
        annotated_frameleft = resultsleft[0].plot()
        cv2.imshow('Left', cv2.resize(annotated_frameleft, (300,300)))
        cv2.moveWindow('Left', 100, 100)
        for resultleft in resultsleft:  # Iterate through the detected objects
          for boxleft in resultleft.boxes:
            class_idleft = int(boxleft.cls[0])
            confidenceleft = boxleft.conf[0]
            if str(class_idleft)=="67":
              if float(confidenceleft)>0.60:
                if shared_dict['moveto'] ==0:
                  print ("LEFT: will process product with label "+shared_dict['label'])
                  shared_dict['label']=class_idleft
                  shared_dict['barcode']="5017007603276"
                  shared_dict['method']="a"
                  shared_dict['moveto']=1
        
        resultsright = model.track(right_image_resized, verbose=False, persist=True)
        annotated_frameright = resultsright[0].plot()
        cv2.imshow('Right', cv2.resize(annotated_frameright, (300,300)))
        cv2.moveWindow('Right', 500, 100)
        for resultright in resultsright:  # Iterate through the detected objects
          for boxright in resultright.boxes:
            class_idright = int(boxright.cls[0])
            confidenceright = boxright.conf[0]
            if str(class_idright)=="67":
              if float(confidenceright)>0.60:
                if shared_dict['moveto'] ==0:
                  print ("RIGHT: will process product with label "+shared_dict['label'])
                  shared_dict['label']=class_idright
                  shared_dict['barcode']="[detected barcode]"
                  shared_dict['method']="a"
                  shared_dict['moveto']=1
    else:
      print("Failed to capture image")

    if cv2.waitKey(1) & 0xFF == ord('q'):
      zed.close()
      cv2.destroyAllWindows()

def robot(shared_dict):
   print ("********************* STARTING ROBOT PROCESS *************************")
   os.nice(0) 
   print(f"Running process robot with niceness: {os.nice(0)} and pid {os.getpid()}")

   file_path_campaign = 'campaign.xml'
   try:
    rootcampaign = ET.parse(file_path_campaign)
    print(f"File '{file_path_campaign}' found and parsed")
   except FileNotFoundError:
    print(f"Error: The file '{file_path_campaign}' does not exist.")
    exit()
   except ET.ParseError:
    print(f"Error: The file '{file_path_campaign}' is not a valid XML file.")
    exit()
   
   file_path_others = 'others.xml'
   try:
    rootothers = ET.parse(file_path_others)
    print(f"File '{file_path_others}' found and parsed")
   except FileNotFoundError:
    print(f"Error: The file '{file_path_others}' does not exist.")
    exit()
   except ET.ParseError:
    print(f"Error: The file '{file_path_others}' is not a valid XML file.")
    exit()
   
   os.system('stty -F /dev/ttyACM0 hupcl')
   port_name = '/dev/ttyACM0'
   baud_rate = 9600
   available_ports = [port.device for port in serial.tools.list_ports.comports()]
   if port_name in available_ports:
      try:
        port = serial.Serial(port_name, baud_rate)
        port.dtr = False
        time.sleep(0.5)  # Give the device time to reset
        port.dtr = True
        expected_packet_size = 42
        def read_exactly(num_bytes):
          data = port.read(num_bytes)
          while len(data) < num_bytes:
            data += port.read(num_bytes - len(data))
          return data
        while True:
            if port.in_waiting >= expected_packet_size:
              packet = read_exactly(expected_packet_size)
              print(f"Received packet: {packet}")
              response = packet
              if len(response) == 42:
                print ("Response length=",len(response)) 
                if response[0] == 0xA5 and response[-1] == 0x5A:
                  data_floats = struct.unpack('<10f', response[1:41])
                  print("Initial Pose:")
                  print(f"X: {data_floats[0]} mm")
                  print(f"Y: {data_floats[1]} mm")
                  print(f"Z: {data_floats[2]} mm")
                  print(f"Rotation: {data_floats[3]} degrees")
                  print(f"Base Angle: {data_floats[4]} degrees")
                  print(f"Long Arm Angle: {data_floats[5]} degrees")
                  print(f"Short Arm Angle: {data_floats[6]} degrees")
                  print(f"Paw Arm Angle: {data_floats[7]} degrees")
                  print(f"Is Grabbing: {data_floats[8]}")
                  print(f"Gripper Angle: {data_floats[9]} degrees")
                  initialx=data_floats[0]
                  initialy=data_floats[1]
                  initialz=data_floats[2]
                  break
                else:
                  print("Invalid response packet. Header or tail bytes are incorrect.")
              else:
                print(f"Unexpected response length: {len(response)} bytes. Expected 42 bytes.")
        while True:
           #print(shared_dict['moveto']) 
           if shared_dict['moveto']==1 or shared_dict['moveto']==2:
             port = serial.Serial(port_name, baud_rate)
             print(f"Moving robot at serial port {port_name}")
             #signal.signal(signal.SIGINT, lambda signal, frame: sys.exit(0))
             print (">>>>>>>>>>>>>moveto =",shared_dict['moveto'])  
             points = []
             if shared_dict['moveto']==1:
               root=rootcampaign
             elif shared_dict['moveto']==2:
               root=rootothers
             for point in root.findall('point'):
               x = float(point.find('x').text)
               y = float(point.find('y').text)
               z = float(point.find('z').text)
               is_grab = 1.0 if point.find('isGrab').text == 'true' else 0.0
               data = []
               while len(data) < 4:
                 print ("waiting for data=",len(data))
                 byte = port.read(1)
                 if len(byte):
                   data.append(byte[0])
               value = struct.unpack('<f', bytes(data))[0]
               print(time.strftime("%a, %d %b %Y %H:%M:%S"), value)
               port.write(bytes([0xa5]))  # Encode to bytes
               port.write(struct.pack('<f', 3.0))
               port.write(struct.pack('<f', 0.0))
               port.write(struct.pack('<f', x))
               port.write(struct.pack('<f', y))
               port.write(struct.pack('<f', z))
               port.write(struct.pack('<f', 0.0))
               port.write(struct.pack('<f', is_grab))
               port.write(struct.pack('<f', 1.0))
               port.write(struct.pack('<f', 0.0))
               port.write(struct.pack('<f', 0.0))
               port.write(bytes([0x5a]))  # Encode to bytes
             
             print (">>>>>>>>>>>>>>>moving robot to initial position of x=",initialx," y=",initialy," z=",initialz)  
             port.write(bytes([0xa5]))  # Encode to bytes
             port.write(struct.pack('<f', 3.0))
             port.write(struct.pack('<f', 0.0))
             port.write(struct.pack('<f', initialx))
             port.write(struct.pack('<f', initialy))
             port.write(struct.pack('<f', initialz))
             port.write(struct.pack('<f', 0.0))
             port.write(struct.pack('<f', 0.0))
             port.write(struct.pack('<f', 1.0))
             port.write(struct.pack('<f', 0.0))
             port.write(struct.pack('<f', 0.0))
             port.write(bytes([0x5a]))  # Encode to bytes
             port.close
             shared_dict['moveto']=0
             print (">>>>>>>>>>>>moveto NOW=",shared_dict['moveto'])
      except serial.serialutil.SerialException as e:
         print(f"Robot not found. Error: {e}")
         exit()
      except KeyboardInterrupt:
        print("KeyboardInterrupt caught.")
        exit()
      finally:
        if port.is_open:
          port.close()
          print(f"Serial port {port_name} closed.")
   else:
      print(f"Robot not found: port {port_name} does not exist or is not connected.")
      exit()
   
def create_pool():
    config = {"host": "[server]","user": "[db user]","password": "[db password]","database": "[db]","port": [db port]}
    pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **config)
    return pool
pool = create_pool()

def speak(shared_dict):
  print ("********************* STARTING SPEAK PROCESS *************************")
  os.nice(0) 
  print(f"Running process speak with niceness: {os.nice(0)} and pid {os.getpid()}")
  while True:  
    if shared_dict['text']!="":
      model = "en_US-lessac-medium.onnx"
      voice = PiperVoice.load(model)
      sample_rate = voice.config.sample_rate
      channels = 1
      dtype = np.int16
      p = pyaudio.PyAudio()
      print ("Will speak ",shared_dict['text']) 
      stream = p.open(format=pyaudio.paInt16,channels=channels,rate=sample_rate,output=True)
      for audio_bytes in voice.synthesize_stream_raw(shared_dict['text']):
        int_data = np.frombuffer(audio_bytes, dtype=dtype)
        stream.write(int_data.tobytes())  # Write bytes to the stream
      stream.stop_stream()
      shared_dict['text']=""
      stream.close()

def processbarcode(shared_dict):
  print ("********************* STARTING PROCESSBARCODE PROCESS *************************")
  os.nice(0) 
  print(f"Running process processbarcode with niceness: {os.nice(0)} and pid {os.getpid()}")
  origin="b"
  idbin=1
  while True:
    #print (" barcode=",shared_dict['barcode']) 
    if shared_dict['barcode']!="":
      print ("Disposing product "+str(shared_dict['label'])+" with barcode "+str(shared_dict['barcode']))
      gmt = time.gmtime()
      timestamp = calendar.timegm(gmt)
      shared_dict['videofilename']=secrets.token_hex(16)
      db_connection = pool.get_connection()
      cursor_barcodes = db_connection.cursor(buffered=False)
      sql_query= "INSERT INTO barcodes (barcode,iduser,origin,timestamp,geo,idbin,videofilename,datetime,method) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
      print ("executing sql ",sql_query)
      val = (shared_dict['barcode'],shared_dict['userid'],origin,timestamp,shared_dict['geo'],idbin,shared_dict['videofilename'],datetime.now(),shared_dict['method'])
      cursor_barcodes.execute(sql_query,val)
      db_connection.commit()
      cursor_barcodes.close()
      db_connection.close() 
      shared_dict['moveto']=1
      print ("Barcode database updated")
      print ("shared_dict['userid']=",shared_dict['userid'])
      if shared_dict['userid']!=0:
        print ("will award points")
        shared_dict['processa']=1
        print ("shared_dict['processa']=",shared_dict['processa'])
      else:
        print ("userid=0, will not award points") 
    shared_dict['barcode']=""
    shared_dict['method']=""
    shared_dict['videofilename']=""

def processpoints(shared_dict,lock):
  print ("********************* STARTING PROCESSPOINTS PROCESS *************************")
  os.nice(-19) 
  print(f"Running process processpoints with niceness: {os.nice(0)} and pid {os.getpid()}")
  host = "[server]"
  user = "[username]"
  password = "[password]"
  while True:
    if shared_dict['processa']==1:
      exit()
      shared_dict['text']="Wait to see how many points you were awarded"
      command="[procedure_to_be_run]"+shared_dict['videofilename']
      print ("Connecting with server with command ",command)
      socket.setdefaulttimeout(30)
      with lock:
        print ("locking variables...")
        shared_dict['text']=""
        shared_dict['barcode']=""
        shared_dict['userid']=0
        shared_dict['moveto'] = 0
        shared_dict['label'] = ""
        shared_dict['loggedin']=0
        with SshMachine(host, user=user, password=password, ssh_opts=["-o", "StrictHostKeyChecking=no"]) as remote:
          print("Authenticated OK")
          resultprocessing = remote[command]()
          #print("Result processing:", resultprocessing)
          found = resultprocessing.split('>>>')[1].split('<<<')[0]
          if int(found) != 0:
            print("Great! You were awarded " + str(found) + " points!")
            shared_dict['text']="Great! You were awarded " + str(found) + " points!"
          else:
            print("No points awarded I am afraid")
            shared_dict['text']="No points awarded I am afraid"
      shared_dict['processa']=0

def login(shared_dict):
  print ("********************* STARTING LOGIN PROCESS *************************")
  os.nice(0) 
  print(f"Running process login with niceness: {os.nice(0)} and pid {os.getpid()}")
  while True:
    if shared_dict['userid']!=0 and shared_dict['loggedin']==0:
      shared_dict['userid']=[user_read]
      print("Checking user with id "+str(shared_dict['userid']))
      db_connection = pool.get_connection()
      cursor_users = db_connection.cursor(buffered=False)
      sqlstring="select id,name from users where id="+str(shared_dict['userid'])
      print ("Executing SQL: "+sqlstring)
      cursor_users.execute(sqlstring)
      rows = cursor_users.fetchall() 
      resultsdb = len(rows) 
      if resultsdb > 0:
        row = rows[0]
        nameofuser=row[1]
        gmt = time.gmtime()
        timestamp = calendar.timegm(gmt)
        videofilename=secrets.token_hex(16)
        cursor_logins = db_connection.cursor(buffered=True)
        sql_query= "INSERT INTO logins (userid,ip,origin,geo,datetime,sessionid,dataehora) VALUES (%s,%s,%s,%s,%s,%s,%s)"
        print ("executing sql ",sql_query)
        val = (shared_dict['userid'],shared_dict['ipnumber'],"b",shared_dict['geologin'],timestamp,videofilename,datetime.now())
        cursor_logins.execute(sql_query,val)
        db_connection.commit()
        cursor_logins.close()
        shared_dict['text']="Hi, "+str(nameofuser)+" dispose now!"
        cursor_users.close()
        db_connection.close()
        shared_dict['loggedin']=1
      else:
         print ("User not found. Will assign 0")
         shared_dict['userid']=0
         shared_dict['loggedin']=0
    
def card(shared_dict):
  print ("********************* STARTING CARD PROCESS *************************")
  os.nice(0) 
  print(f"Running process card with niceness: {os.nice(0)} and pid {os.getpid()}")
  def find_nfc_reader():
    print ("Looking for NFC sensor")
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
      print(f'Checking device: {device.path} - {device.name}')
      if 'NFC' in device.name or 'Reader' in device.name:
        print ("Found device with name: ", device)
        return device
    return None
  
  device = find_nfc_reader()
  if not device:
    print("NFC reader not found. Exiting")
    exit()
  else:
    print(f'Reading from device: {device}')
    
  key_map = {'KEY_0': '0', 'KEY_1': '1', 'KEY_2': '2', 'KEY_3': '3', 'KEY_4': '4','KEY_5': '5', 'KEY_6': '6', 'KEY_7': '7', 'KEY_8': '8', 'KEY_9': '9'}
  nfc_code = ""
  while True:
      for event in device.read_loop():
        if event.type == ecodes.EV_KEY:
          key_event = categorize(event)
          if key_event.keystate == key_event.key_down:
            key_char = key_map.get(key_event.keycode, '')
            if key_char:
              nfc_code += key_char

        if event.type == ecodes.EV_KEY and event.code == ecodes.KEY_ENTER and event.value == 1:
          if nfc_code!="":
            print(f'NFC code: {nfc_code}')
            if shared_dict['userid']==0: 
              shared_dict['userid']=int(nfc_code)
            nfc_code = ""

def touchscreen(shared_dict):
  print ("********************* STARTING TOUCHSCREEN PROCESS *************************")
  os.nice(0) 
  print(f"Running process card with niceness: {os.nice(0)} and pid {os.getpid()}")
  # --- Find Waveshare touchscreen directly ---
  touchscreen = None
  devices = [InputDevice(fn) for fn in list_devices()]
  for dev in devices:
    if "waveshare" in dev.name.lower():
        print(f"[INFO] Found touchscreen: {dev.name} at {dev.path}")
        touchscreen = dev
        break
  if not touchscreen:
    print("[ERROR] No Waveshare touchscreen detected. Exiting.")
    sys.exit(1)

  # --- Pygame setup ---
  pygame.init()
  WIDTH, HEIGHT = 800, 480
  screen = pygame.display.set_mode((WIDTH, HEIGHT))
  pygame.display.set_caption("Point of Disposal Menu")
  font_title = pygame.font.SysFont(None, 70)
  font_button = pygame.font.SysFont(None, 50)
  clock = pygame.time.Clock()

  # --- Buttons ---
  buttons = ["Dispose now","Check rewards","Register","Know more!"]
  button_rects = []
  spacing = 20
  btn_width, btn_height = 400, 70
  start_y = 150
  for i, text in enumerate(buttons):
    x = (WIDTH - btn_width) // 2
    y = start_y + i * (btn_height + spacing)
    button_rects.append(pygame.Rect(x, y, btn_width, btn_height))

  finger_x, finger_y = WIDTH // 2, HEIGHT // 2
  finger_down = False

  # --- Main loop ---
  while True:
    # Handle window events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit(0)
    # Read touchscreen events
    r, w, e = select.select([touchscreen.fd], [], [], 0)
    if touchscreen.fd in r:
        for event in touchscreen.read():
            if event.type == ecodes.EV_ABS:
                if event.code in [ecodes.ABS_MT_POSITION_X, ecodes.ABS_X]:
                    finger_x = event.value
                elif event.code in [ecodes.ABS_MT_POSITION_Y, ecodes.ABS_Y]:
                    finger_y = event.value
            elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                finger_down = event.value == 1
                if not finger_down:  # On finger release
                    for idx, rect in enumerate(button_rects):
                        if rect.collidepoint(finger_x, finger_y):
                            print(f"[INFO] Button tapped: {buttons[idx]}")

    # Draw background
    screen.fill((30, 30, 30))
    # Draw title
    title_surf = font_title.render("Point of Disposal (POD)", True, (255, 255, 255))
    screen.blit(title_surf, ((WIDTH - title_surf.get_width()) // 2, 40))
    # Draw buttons
    for i, rect in enumerate(button_rects):
        color = (70, 70, 70)
        if rect.collidepoint(finger_x, finger_y) and finger_down:
            color = (100, 0, 0)
        pygame.draw.rect(screen, color, rect, border_radius=10)
        text_surf = font_button.render(buttons[i], True, (255, 255, 255))
        screen.blit(
            text_surf,
            (
                rect.x + (rect.width - text_surf.get_width()) // 2,
                rect.y + (rect.height - text_surf.get_height()) // 2,
            ),
        )
    pygame.display.flip()
    clock.tick(60)

def init():
  lock = Lock()  
  ipnumero = socket.gethostbyname(socket.gethostname())
  if ipnumero != "":
        my_location = geocoder.ip('me')
        try:
            latitude = my_location.geojson['features'][0]['properties']['lat']
            longitude = my_location.geojson['features'][0]['properties']['lng']
        except IndexError:
            print("Error obtaining geolocation, will use generic")
            latitude = 0
            longitude = 0
  geonumero = str(latitude) + "," + str(longitude)
  geologinnumero = "Latitude: " + str(latitude) + ",Longitude: " + str(longitude)
  print("Bin location:", geonumero)
  manager = mp.Manager()
  shared_dict = manager.dict()
  shared_dict['userid'] = 0
  shared_dict['moveto'] = 0
  shared_dict['barcode'] = ""
  shared_dict['geologin'] = geologinnumero
  shared_dict['geo'] = geonumero
  shared_dict['ipnumber'] = ipnumero
  shared_dict['label'] = ""
  shared_dict['text'] = ""
  shared_dict['method']=""
  shared_dict['videofilename']=""
  shared_dict['processa']=0
  shared_dict['loggedin']=0
  
  sink_name="alsa_output.usb-GeneralPlus_USB_Audio_Device-00.analog-stereo"
  try:
    result = subprocess.run(['pactl', 'set-default-sink', sink_name], stderr=subprocess.PIPE)
    if result.returncode != 0:
      raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
      print(f"Default sink set to: {sink_name}")
  except subprocess.CalledProcessError as e:
    print(f"Error setting default sink: {e.stderr.decode('utf-8').strip()}")
    
  processpoints_process= mp.Process(target=processpoints, args=(shared_dict,))
  robot_process = mp.Process(target=robot, args=(shared_dict,))
  datalogic_process = mp.Process(target=datalogic, args=(shared_dict,))
  zed_process = mp.Process(target=zed, args=(shared_dict,))
  card_process = mp.Process(target=card, args=(shared_dict,))
  speak_process = mp.Process(target=speak, args=(shared_dict,))
  login_process = mp.Process(target=login, args=(shared_dict,))
  processbarcode_process = mp.Process(target=processbarcode, args=(shared_dict,))
  touchscreen_process=mp.Process(target=touchscreen, args=(shared_dict,))

  processpoints_process.start()
  robot_process.start()
  datalogic_process.start()
  zed_process.start()
  card_process.start()
  speak_process.start()
  login_process.start()
  processbarcode_process.start()
  touchscreen_process.start()
  
  processpoints_process.join()
  robot_process.join()
  datalogic_process.join()
  zed_process.join()
  card_process.join()
  speak_process.join()
  login_process.join()
  processbarcode_process.join()
  touchscreen_process.join()

if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG)
  mp.set_start_method('spawn')
  current_method = mp.get_start_method()
  print(f"Current start method: {current_method}")
  init()
