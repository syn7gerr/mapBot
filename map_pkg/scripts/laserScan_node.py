#!/usr/bin/python
#stepper framework by petebachant
#scanning and changes made by Morgan Dykshorn
#imports necessary libraries
import time
import math
#import rospy
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.GPIO as GPIO
from Adafruit_I2C import Adafruit_I2C

def initialize_pins(pins):
	for pin in pins:
		GPIO.setup(pin, GPIO.OUT)

def set_all_pins_low(pins):
	for pin in pins:
		GPIO.output(pin, GPIO.LOW)
		
def wavedrive(pins, pin_index):
	for i in range(len(pins)):
		if i == pin_index:
			GPIO.output(pins[i], GPIO.HIGH)
		else:
			GPIO.output(pins[i], GPIO.LOW)

def fullstep(pins, pin_index):
	"""pin_index is the lead pin"""
	GPIO.output(pins[pin_index], GPIO.HIGH)
	GPIO.output(pins[(pin_index+3) % 4], GPIO.HIGH)
	GPIO.output(pins[(pin_index+1) % 4], GPIO.LOW)
	GPIO.output(pins[(pin_index+2) % 4], GPIO.LOW)


class laserScan(object):
	def __init__(self, steps_per_rev=2048.0,
				 pins=["P9_27", "P8_15", "P8_11", "P8_12"]):

		#sets lidar lite addresses
		self.address = 0x62
		self.distWriteReg = 0x00
		self.distWriteVal = 0x04
		self.distReadReg1 = 0x8f
		self.distReadReg2 = 0x10

		#initilizes the i2c bus on address lidar lite address on bus 1
		self.i2c = Adafruit_I2C(self.address, 1)
		
		#creates pins for the stepper motors
		self.pins = pins
		
		#initlizes the pins for stepper
		initialize_pins(self.pins)
		set_all_pins_low(self.pins)
		
		#sets angle to 0
		self.angle = 0
		
		# Initialize stepping mode
		self.drivemode = fullstep

		#sets up ADC
		ADC.setup()
		#cretes a value for the threshold
		self.threshold = .2
		#creates a variable for the distance measurment
		self.distance = 0
		#creates a variable for the last ir sensor read
		self.lastval = 1

	def calibrate(self):
		#sets angle to 1 so loop will run
		self.angle = 1.0


		while self.angle!=0:

			for pin_index in range(len(self.pins)):
				self.drivemode(self.pins, pin_index)
				#waits for .0025 seconds keeping the sensor reading at 100hz
				time.sleep(.0025)
				#checks for when the sensor triggers 0 angle calibration
				#reads value from sensor
				rotateVal = ADC.read("P9_39")
				if rotateVal > self.threshold and self.lastval<self.threshold:
					self.angle = 0
				self.lastval = rotateVal			
		set_all_pins_low(self.pins)	

	
	def scan(self):
		#initilizes a count for number of datapoints
		count = 0
		changes angle temporarily so loop will run
		self.angle = .01
		#creates a variable that returns 1 when the scan completes
		scanComplete = 0
		#runs indefinitely
		while count<400 or self.angle != 0:
	
			for pin_index in range(len(self.pins)):
				self.drivemode(self.pins, pin_index)
				
				#writes to the LIDAR to take a reading
				#writes to the register that takes measurment
				self.i2c.write8(self.distWriteReg, self.distWriteVal)
				#waits for 'x' seconds to control motor speed and prevent sensor overpolling(minimum sleep time is .0025)
				time.sleep(.01)
				
				#checks for when the sensor triggers 0 angle calibration
				#reads value from sensor
				rotateVal = ADC.read("P9_39")
				#checks if the sensor is over the threshold but the last value is under the threshold
				#if both are true the sensor has just been passe dan should now reset
				if rotateVal > self.threshold and self.lastval<self.threshold:
					self.angle = 0
				else:
					self.angle = self.angle + .9
				self.lastval = rotateVal
				#reads distance from Lidar
				dist1 = self.i2c.readU8(self.distReadReg1)
				dist2 = self.i2c.readU8(self.distReadReg2)
				#shifts bits to get correct distance
				self.distance = (dist1<<8) + dist2

				print self.angle, self.distance, count
				
				count = count+1

		set_all_pins_low(self.pins)
		scanComplete = 1
		return scanComplete	


if __name__ == '__main__':

	#creates an instance of the class
	lScan = laserScan()

	lScan.calibrate()

	complete = lScan.scan()
	print complete