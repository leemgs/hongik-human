#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# config.py 파일의 한글들을 읽기위해 위의 내용이 선언되어야 한다. 

# @USAGE
# python social_distance_detector.py --input pedestrians.mp4
# python social_distance_detector.py --input pedestrians.mp4 --output output.avi
# @Requirement
# sudo apt install omxplayer
# sudo apt install vlc
# sudo apt install mplayer
# install mysql library for python 3 
# sudo pip3 install mysqlclient


# import the necessary packages
from pyimage import social_distancing_config as config
from pyimage.detection import detect_people
from scipy.spatial import distance as dist
import numpy as np
import argparse
import imutils
import cv2
import os 
import time

import MySQLdb
import config as cfg
from datetime import datetime

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--input", type=str, default="",
	help="path to (optional) input video file")
ap.add_argument("-o", "--output", type=str, default="",
	help="path to (optional) output video file")
ap.add_argument("-d", "--display", type=int, default=1,
	help="whether or not output frame should be displayed")
args = vars(ap.parse_args())

# load the COCO class labels our YOLO model was trained on
labelsPath = os.path.sep.join([config.MODEL_PATH, "coco.names"])
LABELS = open(labelsPath).read().strip().split("\n")

# derive the paths to the YOLO weights and model configuration
weightsPath = os.path.sep.join([config.MODEL_PATH, "yolov3.weights"])
configPath = os.path.sep.join([config.MODEL_PATH, "yolov3.cfg"])

# load our YOLO object detector trained on COCO dataset (80 classes)
print("[INFO] loading YOLO from disk...")
net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)

# check if we are going to use GPU
if config.USE_GPU:
	# set CUDA as the preferable backend and target
	print("[INFO] setting preferable backend and target to CUDA...")
	net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
	net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

# determine only the *output* layer names that we need from YOLO
ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# initialize the video stream and pointer to output video file
print("[INFO] accessing video stream...")
vs = cv2.VideoCapture(args["input"] if args["input"] else 0)

vs.set(cv2.CAP_PROP_FPS, int(5))
print("[INFO] Frame rate : {0}".format(vs.get(cv2.CAP_PROP_FPS)))

writer = None

# loop over the frames from the video stream
while True:
	# read the next frame from the file
	(grabbed, frame) = vs.read()

	# if the frame was not grabbed, then we have reached the end
	# of the stream
	if not grabbed:
		break

	# resize the frame and then detect people (and only people) in it
	frame = imutils.resize(frame, width=700)
	results = detect_people(frame, net, ln,
		personIdx=LABELS.index("person"))

	# initialize the set of indexes that violate the minimum social
	# distance
	violate = set()

	# ensure there are *at least* two people detections (required in
	# order to compute our pairwise distance maps), 2M(social distancing)
	if len(results) >= 2:
		# extract all centroids from the results and compute the
		# Euclidean distances between all pairs of the centroids
		centroids = np.array([r[2] for r in results])
		D = dist.cdist(centroids, centroids, metric="euclidean")

		# loop over the upper triangular of the distance matrix
		for i in range(0, D.shape[0]):
			for j in range(i + 1, D.shape[1]):
				# check to see if the distance between any two
				# centroid pairs is less than the configured number
				# of pixels
				if D[i, j] < config.MIN_DISTANCE:
					# update our violation set with the indexes of
					# the centroid pairs
					violate.add(i)
					violate.add(j)

	# loop over the results
	for (i, (prob, bbox, centroid)) in enumerate(results):
		# extract the bounding box and centroid coordinates, then
		# initialize the color of the annotation
		(startX, startY, endX, endY) = bbox
		(cX, cY) = centroid
		color = (0, 255, 0)

		# if the index pair exists within the violation set, then
		# update the color
		if i in violate:
			color = (0, 0, 255)

		# draw (1) a bounding box around the person and (2) the
		# centroid coordinates of the person,
		cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)
		cv2.circle(frame, (cX, cY), 5, color, 1)



	# Combine database saveing: start -------------------------------
	print('정보들을 데이타베이스의 테이블에 삽입을 시도합니다.')

	# Mysql Database: Insert Into....
	# @see 
	# https://www.tutorialspoint.com/python/python_database_access.htm
	# https://www.w3schools.com/python/python_mysql_insert.asp


	timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	# print(timestamp)

	# https://stackoverflow.com/questions/6202726/writing-utf-8-string-to-mysql-with-python
	# Open database connection
	db = MySQLdb.connect(cfg.mysql['host'],cfg.mysql['user'],cfg.mysql['passwd'],cfg.mysql['db'],charset='utf8')

	# Prepare a cursor object using cursor() method
	cursor = db.cursor()

	# Prevent broken korean statements
	db.query("set names utf8;")
	db.query("set character_set_connection=utf8;")
	db.query("set character_set_server=utf8;")
	db.query("set character_set_client=utf8;")
	db.query("set character_set_results=utf8;")
	db.query("set character_set_database=utf8;")


	# Run a mysql command
	violation=int(len(violate))
	#print (" Current Violations: ", timestamp, int(len(violate)))
	print ("Timestamp: ", timestamp , "The number of violators:", violation)
	if violation >= cfg.covid_sd['violator_num']:
		try:
			sql = """INSERT INTO covid_sd (time, site, location, violation) VALUES (%s, %s, %s, %s) """
			# https://stackoverflow.com/questions/62656579/why-im-getting-unicodeencodeerror-charmap-codec-cant-encode-character-u2
			# for python2
			record_tuple = (timestamp, cfg.covid_sd['site'], cfg.covid_sd['location'], violation)
			# for python3
			#record_tuple = (timestamp, cfg.covid_sd['site'].encode('utf-8').decode('ascii', 'ignore'), cfg.covid_sd['location'].encode('utf-8').decode('ascii', 'ignore'), violation)
			cursor.execute(sql, record_tuple)
			db.commit()
			cursor.close()
			print("Record inserted successfully into a table.")
		except:
			db.rollback()
			print("Failed to insert a record into a table.")
   
		# disconnect from server
		db.close()

	# Combine database saveing: end    -------------------------------


	# play audio notice:start-----------------------------------------
	if violation >= 50:
		# Note that mplayer is not good in RPI4. It results in "Audio device got stuck!" error.
		# audio out options of mplayer: -ao alsa , -ao pluse
		# cmd = "mplayer -ao pulse " + search_path + audio_file
		audio_file = "audio-notice/50.m4a" 
		cmd = "cvlc -A alsa,none --alsa-audio-device default " + audio_file + " vlc://quit"
		print ("[DEBUG] Succeeded, command: %s." % cmd)
		print ("[DEBUG] We found audio file.")
		print ("[DEBUG] Let's play the audio file:" , audio_file)
		os.system(cmd)

	elif violation >= 40:
		audio_file = "audio-notice/40.m4a" 
		cmd = "cvlc -A alsa,none --alsa-audio-device default " + audio_file + " vlc://quit"
		print ("[DEBUG] Succeeded, command: %s." % cmd)
		print ("[DEBUG] We found audio file.")
		print ("[DEBUG] Let's play the audio file:" , audio_file)
		os.system(cmd)

	elif violation >= 30:
		audio_file = "audio-notice/30.m4a" 
		cmd = "cvlc -A alsa,none --alsa-audio-device default " + audio_file + " vlc://quit"
		print ("[DEBUG] Succeeded, command: %s." % cmd)
		print ("[DEBUG] We found audio file.")
		print ("[DEBUG] Let's play the audio file:" , audio_file)
		os.system(cmd)

	elif violation >= 20:
		audio_file = "audio-notice/20.m4a" 
		cmd = "cvlc -A alsa,none --alsa-audio-device default " + audio_file + " vlc://quit"
		print ("[DEBUG] Succeeded, command: %s." % cmd)
		print ("[DEBUG] We found audio file.")
		print ("[DEBUG] Let's play the audio file:" , audio_file)
		os.system(cmd)

	elif violation >= 1:
		audio_file = "audio-notice/10.m4a" 
		cmd = "cvlc -A alsa,none --alsa-audio-device default " + audio_file + " vlc://quit"
		print ("[DEBUG] Succeeded, command: %s." % cmd)
		print ("[DEBUG] We found audio file.")
		print ("[DEBUG] Let's play the audio file:" , audio_file)
		os.system(cmd)
	else:   
		print ("[DEBUG] Now, people keep social distancing rule very well.")
		audio_file = "audio-notice/00.m4a" 
		cmd = "cvlc -A alsa,none --alsa-audio-device default " + audio_file + " vlc://quit"
		print ("[DEBUG] Succeeded, command: %s." % cmd)
		print ("[DEBUG] We found audio file.")
		print ("[DEBUG] Let's play the audio file:" , audio_file)
		os.system(cmd)

	# play audio notice:end -----------------------------------------

	# Delays for 5 seconds. You can also use a float value.
	time.sleep(5)
	print("Sleeping 5 seconds .....")   

	# draw the total number of social distancing violators on the output frame
	text = "Social Distancing Plus(Violator): {}".format(len(violate))
	cv2.putText(frame, text, (10, frame.shape[0] - 25),
		cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 3)

	# check to see if the output frame should be displayed to our screen
	if args["display"] > 0:
		# display obtained image window in  the output frame (GUI APP)
		print("Running a GUI application .....")   
		cv2.imshow("CAM_Window", frame)
		#cv2.imshow("Changed", frame)
                # if you want to change a waiting time (ms) between frames, change cv2.waitKey(1)
		key = cv2.waitKey(10) & 0xFF

		# if the `q` key was pressed, break from the loop
		if key == ord("q"):
			break

	# if an output video file path has been supplied and
        # the video writer has not been initialized, do so now
        # if you want to change FPS(frame per seconds), change the value 25.
	# writer = cv2.VideoWriter(args["output"], fourcc, 25,
	#           (frame.shape[1], frame.shape[0]), True)
	if args["output"] != "" and writer is None:
		# initialize our video writer
		fourcc = cv2.VideoWriter_fourcc(*"MJPG")
		writer = cv2.VideoWriter(args["output"], fourcc, 25,
			(frame.shape[1], frame.shape[0]), True)

	# if the video writer is not None, write the frame to the output video file
	if writer is not None:
		writer.write(frame)
