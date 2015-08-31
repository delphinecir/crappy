from ._meta import cameraSensor
import numpy as np
import cv2
import time
from multiprocessing import Process,Pipe
from matplotlib.widgets import RectangleSelector
import matplotlib.pyplot as plt
import matplotlib.animation as animation
#from matplotlib import rcParams
from matplotlib.widgets import Slider, Button


#class Interface(Frame):

	#def __init__(self, root, **kwargs):
		##print "1"
		#Frame.__init__(self, root, width=1000, height=1000, **kwargs)
		##root.title("Camera")
		##police=tkFont.Font(self, size=15, family='Time')
		##self.directory = os.getcwd()
		#frame = Frame(root, width=400, borderwidth=2,relief=GROOVE) # create a frame in canvas(p1)
		##print "2"
		##self.portLabel = Label(frame, text="Camera:") # create a label 
		##self.cameraSelection= Tix.StringVar() # create a variable, it will contain port selection 
		###print "3"
		##self.cameraCombo= Tix.ComboBox(frame, editable=1, dropdown=1, variable=self.cameraSelection) # create a combobox, it will contain names of ports 
		##self.cameraCombo.entry.config(state='readonly') # configure the combobox in read only
		##self.cameraCombo.insert(Tix.END, 'jai')
		##self.cameraCombo.insert(Tix.END, 'ximea')
		###print "4"
		##self.dirLabel = Label(frame, text="Directory:") #create a label
		##self.directoryVar = Tix.StringVar()
		##self.dirEntry = Entry(frame, textvariable=self.directoryVar)
		##self.directoryVar.set(self.directory)
		###print "5"
		##self.camNumLabel = Label(frame, text="Camera number:") #create a label
		##self.camNumVar = 0
		##self.camNumSpinbox= Spinbox(frame, from_=0, to=10)
		###print "6"
		### defining options for opening a directory
		##self.dir_opt = options = {}
		##options['mustexist'] = True
		##options['parent'] = root
		##print "7"
		##self.File = Tix.DirSelectDialog(root) ##### CRASH the script, to be fixed
		##print "8"
		##self.pathSelectButton = Button(frame, text="Browse...", command=self.askdirectory)
		#self.okButton = Button(root, text="OK", command=self._close)
		###print "9"
		#frame.grid(padx=10,pady=10) # 
		##self.portLabel.grid(row=1, column=0, sticky= "sw",padx=10,pady=10)
		##self.cameraCombo.grid(row=1, column=1, sticky= "sw",padx=10,pady=10)
		##self.camNumLabel.grid(row=2, column=0, sticky= "w",padx=10,pady=10)
		##self.camNumSpinbox.grid(row=2, column=1, sticky= "w",padx=10,pady=10)
		##self.dirLabel.grid(row=3, column=0, sticky= "w",padx=10,pady=10)
		##self.dirEntry.grid(row=3, column=1, sticky= "w",padx=10,pady=10)
		##self.pathSelectButton.grid(row=3, column=2, sticky= "sw",padx=10,pady=10)
		#self.okButton.grid(row=3, column=2, sticky= "sw",padx=10,pady=10 )

	#def _close(self):
		##self.camNumVar = int(self.camNumSpinbox.get())
		##if not self.cameraSelection.get() == "":
		#self.destroy()
		#self.quit()
		#self.master.quit()


	

class XimeaSensor(cameraSensor.CameraSensor):
	"""
	Camera class for ximea devices, this class should inherit from CameraObject
	"""
	def __init__(self, numdevice=0, exposure=10000, gain=0, width=2048, height=2048, xoffset=0, yoffset=0, framespersec=None, external_trigger=False, data_format=0):
		self.quit=False
		self.exposure= exposure
		self.gain=gain
		self.FPS=framespersec
		self.framespersec=self.FPS
		self.numdevice = numdevice
		self.width=width
		self.height=height
		self.xoffset=xoffset
		self.yoffset=yoffset
		self.external_trigger=external_trigger
		self.data_format=data_format
#	initialisation:
		recv_pipe,send_pipe=Pipe()
		proc_test=Process(target=self.interface,args=(send_pipe,))
		proc_test.start()
		data=recv_pipe.recv()
		#print data
		self.exposure,self.gain,self.width,self.height,self.xoffset,self.yoffset=data[:]
		proc_test.terminate()
		self.new()
	
	def interface(self, send_pipe):
		self.new()
		self.camera_setup()
		self.width,self.height,self.xoffset,self.yoffset=self.set_ZOI()
		self.close()
		send_pipe.send([self.exposure,self.gain,self.width,self.height,self.xoffset,self.yoffset])		
		
		
	def new(self):
		"""
		this method opens the ximea device. Ximea devices start at 1100. 1100 => device 0, 1101 => device 1
		And return a camera object
		"""
		self.cam = cv2.VideoCapture(cv2.CAP_XIAPI + self.numdevice) # open the ximea device Ximea devices start at 1100. 1100 => device 0, 1101 => device 1 

		if self.external_trigger==True:	# this condition activate the trigger mode
			self.cam.set(cv2.CAP_PROP_XI_TRG_SOURCE,1)
			self.cam.set(cv2.CAP_PROP_XI_GPI_SELECTOR,1)
			self.cam.set(cv2.CAP_PROP_XI_GPI_MODE,1)
			
		self.cam.set(cv2.CAP_PROP_XI_DATA_FORMAT,self.data_format) #0=8 bits, 1=16(10)bits, 5=8bits RAW, 6=16(10)bits RAW	

		if self.data_format ==1 or self.data_format==6: #increase the FPS in 10 bits
			self.cam.set(cv2.CAP_PROP_XI_OUTPUT_DATA_BIT_DEPTH,10)
			self.cam.set(cv2.CAP_PROP_XI_DATA_PACKING,1)
		
		self.cam.set(cv2.CAP_PROP_XI_AEAG,0)#auto gain auto exposure
		#print "height : ",self.height
		self.cam.set(cv2.CAP_PROP_FRAME_WIDTH,self.width);	# doesn't work for this one
		self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT,self.height); # reducing this one allows one to increase the FPS
		self.cam.set(cv2.CAP_PROP_XI_OFFSET_Y,self.yoffset)
		self.cam.set(cv2.CAP_PROP_XI_OFFSET_X,self.xoffset)
		
		self.cam.set(cv2.CAP_PROP_EXPOSURE,self.exposure) # setting up exposure
		self.cam.set(cv2.CAP_PROP_GAIN,self.gain) #setting up gain
		ret, frame= self.cam.read()
	
	def getImage(self):
		"""
		This method get a frame on the selected camera and return a ndarray 
		If the camera breaks down, it reinitializes it, and tries again.
		"""
		try:
			ret, frame = self.cam.read()

		except KeyboardInterrupt:
			print "KeyboardInterrupt, closing camera ..."
			self.close()
			self.quit=True

		try:
			if ret:
				return frame
			elif not(self.quit):
				self.close()
				self.new() # Reset the camera instance
				return self.getImage()
		except UnboundLocalError: # if ret doesn't exist, because of KeyboardInterrupt
			pass

			
	def setExposure(self, exposure):
		"""
		this method changes the exposure of the camera
		and set the exposure attribute
		"""
		self.cam.set(cv2.CAP_PROP_EXPOSURE,exposure)
		self.exposure = exposure
	
	def close(self):
		"""
		This method close properly the frame grabber
		It releases the allocated memory and stops the acquisition
		"""
		print "closing camera..."
		if self.cam.isOpened():
			self.cam.release()
			print "cam closed"
		else:
			print "cam already closed"
		

	def reset_ZOI(self):
		self.width=2048
		self.height=2048
		self.xoffset=0
		self.yoffset=0
		self.set_offset_y(self.xoffset)
		self.set_offset_x(self.xoffset)
		self.set_height(self.height)
		self.set_width(self.width)
		

	def set_ZOI(self):
		"""
		This method close properly the frame grabber
		It releases the allocated memory and stops the acquisition
		"""
		image=self.getImage()
		try:
			xmin, xmax, ymin, ymax=self.ZOI_selection(image)
		except: 
			xmin=self.xoffset
			xmax=self.width+self.xoffset
			ymin=self.yoffset
			ymax=self.height+self.yoffset
		#print "x : ",xmin,xmax
		xmin=(int(xmin)-int(xmin)%4) # ensure %2
		xmax=(int(xmax)-int(xmax)%4)
		ymin=(int(ymin)/2)*2
		ymax=(int(ymax)/2)*2
		cx=xmax-xmin
		cy=ymax-ymin
		self.set_height(cy)
		self.set_width(cx)
		self.set_offset_y(ymin)
		self.set_offset_x(xmin)
		return cx,cy,xmin,ymin

	def set_height(self,height):
		self.height=height
		self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT,height)
	
	def set_width(self,width):
		self.width=width
		self.cam.set(cv2.CAP_PROP_FRAME_WIDTH,width)

	def set_offset_y(self,yoffset):
		self.yoffset=yoffset
		self.cam.set(cv2.CAP_PROP_XI_OFFSET_Y,yoffset)
		
	def set_offset_x(self,xoffset):
		self.xoffset=xoffset
		self.cam.set(cv2.CAP_PROP_XI_OFFSET_X,xoffset)
		
	def ZOI_selection(self,image):
		rectprops = dict(facecolor='red', edgecolor = 'red', alpha=0.5, 
				fill=True)

		def line_select_callback(eclick, erelease):
			global xmin, ymin, xmax, ymax
			x1, y1 = eclick.xdata, eclick.ydata
			x2, y2 = erelease.xdata, erelease.ydata
			xmin=round(min(x1,x2))
			xmax=round(max(x1,x2))
			ymin=round(min(y1,y2))
			ymax=round(max(y1,y2))
			
		def toggle_selector(event):
			toggle_selector.RS.set_active(False)
			#if event.key in ['Q', 'q'] :
				#toggle_selector.RS.set_active(False)
				#plt.close()

		fig, current_ax = plt.subplots()
		plt.imshow(image,cmap='gray')  # plot something

		toggle_selector.RS = RectangleSelector(current_ax, line_select_callback,
							drawtype='box', useblit=True,
							button=[1,3], # don't use middle button
							minspanx=5, minspany=5,rectprops=rectprops,
							spancoords='pixels')

		plt.show()
		return xmin, xmax, ymin, ymax
		
	def camera_setup(self):
		### initialising the histogram
		if self.cam.get(cv2.CAP_PROP_XI_DATA_FORMAT)==0 or self.cam.get(cv2.CAP_PROP_XI_DATA_FORMAT)==5:
			x=np.arange(0,256,4)
		if self.cam.get(cv2.CAP_PROP_XI_DATA_FORMAT)==1 or self.cam.get(cv2.CAP_PROP_XI_DATA_FORMAT)==6:
			x=np.arange(0,1024,4)
		hist=np.ones(np.shape(x))
		frame = self.getImage()
		### initialising graph and axes
		rat = 0.7
		Width=7
		Height=7.
		fig=plt.figure(figsize=(Height, Width))
		axim = fig.add_axes([0.15, 0.135, rat, rat*(Height/Width)]) # Image frame
		cax = fig.add_axes([0.17+rat, 0.135, 0.02, rat*(Height/Width)]) # colorbar frame
		axhist=fig.add_axes([0.15,(0.17+rat),rat,0.1]) # histogram frame
		axhist.set_xlim([0,max(x)]) #set histogram limit in x...
		axhist.set_ylim([0,1]) # ... and y

		im = axim.imshow(frame,cmap=plt.cm.gray,interpolation='nearest') # display the first image
		li,= axhist.plot(x,hist) #plot first histogram
		cb = fig.colorbar(im, cax=cax) #plot colorbar
		cax.axis('off')

		### define cursors here
		axcolor = 'lightgoldenrodyellow'
		axExp = plt.axes([0.15, 0.02,rat, 0.03], axisbg=axcolor) # define position and size
		sExp = Slider(axExp, 'Exposure', 200, 50000, valinit=self.exposure) #Exposition max = 1000000 # define slider with previous position and size
		axGain= plt.axes([0.15, 0.07,rat, 0.03], axisbg=axcolor)
		sGain = Slider(axGain, 'Gain', -1, 6, valinit=self.gain)

		def update(val): # this function updates the exposure and gain values 
			self.exposure=sExp.val
			self.gain=sGain.val
			self.cam.set(cv2.CAP_PROP_EXPOSURE,sExp.val)
			self.cam.set(cv2.CAP_PROP_GAIN,sGain.val)
			fig.canvas.draw_idle()
		
		sExp.on_changed(update) # call for update everytime the cursors change
		sGain.on_changed(update)

		### Main
		def get_frame(i):
			frame = self.getImage() # read a frame
			if i == 1:
				cax.axis('on')
			im.set_data(frame) #change previous image by new frame
			im.set_clim([frame.min(), frame.max()]) # re-arrange colorbar limits
			histogram=cv2.calcHist([frame],[0],None,[len(x)],[0,max(x)]) # evalute new histogram
			histogram=np.sqrt(histogram) # this operation aims to improve the histogram visibility (avoid flattening)
			li.set_ydata((histogram-histogram.min())/(histogram.max()-histogram.min())) # change previous histogram
			return cax, axim , axhist # return the values that need to be updated

		ani = animation.FuncAnimation(fig, get_frame, interval=200, frames=20, blit=False) # This function call the get_frame function to update averything in the figure.
		plt.show()
		plt.close()

	
	def __str__(self):
		"""
		This method prints out the attributes values
		"""
		return " Exposure: {0} \n FPS: {1} \n Numdevice: {2} \n Width: {3} \n Height: {4} \n X offset: {5} \n Y offset: {6}".format(self.exposure, self.FPS, self.numdevice, self.width, self.height, self.xoffset, self.yoffset)