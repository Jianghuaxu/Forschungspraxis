#-*- coding: utf-8 -*-

# Presence and instant messaging
#!/usr/bin/python
from Tkinter import *
import pjsua
import datetime
import time
import pjsua as pj
import threading
import sys

LOG_LEVEL = 3
pending_pres = None
pending_uri = None

def log_cb(level, str, len):
	print str
	
#Class to receive notifications on account's events
class MyAccountCallback(pj.AccountCallback):
	def __init__(self, account=None):
		pj.AccountCallback.__init__(self, account)
		
    #Notification when incoming SUBSCRIBE request is received. 
	def on_incoming_subscribe(self, buddy, from_uri, contact_uri, pres):
		global pending_pres, pending_uri
		# Allow buddy to subscribe to our presence
		if buddy:
			return (200, None)
		print 'Incoming SUBSCRIBE request from', from_uri
		print 'Press "A" to accept and add, "R" to reject the request'
		pending_pres = pres
		pending_uri = from_uri
		return (202, None)
		
	def wait(self):
		self.sem = threading.Semaphore(0)
		self.sem.acquire()
		
	def on_reg_state(self):
		if self.sem:
			if self.account.info().reg_status >= 200:
				self.sem.release()
				
#This class can be used to receive notifications about Buddy's presence status change.				
class MyBuddyCallback(pj.BuddyCallback):
	def __init__(self, buddy=None):
		pj.BuddyCallback.__init__(self, buddy)

	def on_state(self):
		print "Buddy", self.buddy.info().uri, "is",
		print self.buddy.info().online_text
		
	#Notification that incoming instant message is received from this buddy.
	def on_pager(self, mime_type, body):
		#print "Instant message from", self.buddy.info().uri,
		#print "(", mime_type, "):"
		#print body, " is reveived at :",datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')
		
		#received messages will be stored in locol computer with specific diretory
		message=body+" is received at : *"+datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S.%f')+"*"+"\n"
		
		#calculate the transport delay for test(test message start with "M")
		if body[0]=="M":
			num_r_split=message.split('*')
			if float(num_r_split[3].split(':')[-2])==float(num_r_split[1].split(':')[-2]):
				delay=float(num_r_split[3].split(':')[-1])-float(num_r_split[1].split(':')[-1])
			else:
				delay=float(num_r_split[3].split(':')[-1])-float(num_r_split[1].split(':')[-1])+60
		else:
			delay=None
			
		text_msglist.insert(END, self.buddy.info().uri+"\n",'tag_a')
		text_msglist.tag_config('tag_a',foreground='red',underline=1)
		text_msglist.insert(END,message)
		text_msglist.see(END)
		handle=open("/Users/Jianghua/Desktop/a.txt","a")
		handle_1=open("/Users/Jianghua/Desktop/delay.txt","a")
		write_message=message+"delay is : "+str(delay)+"s"+"\n"
		handle.write(write_message)
		handle_1.write(str(delay)+"\n")
		handle.close()
		handle_1.close()
		
	def on_pager_status(self, body, im_id, code, reason):
		if code >= 300:
			print "Message delivery failed for message",
			print body, "to", self.buddy.info().uri, ":", reason

	def on_typing(self, is_typing):
		if is_typing:
			print self.buddy.info().uri, " is typing"
			root.title(var_title+"is typing")
			time.sleep(5)
			root.title(var_title)
			
		else:
			print self.buddy.info().uri, "stops typing"
			
#create a radio_button for setting online_status of the created account
class RB:
	def __init__(self,master):
		self.master=master
		self.var=StringVar()
		self.var_entry=StringVar()
		
	def sel(self):
		if self.var.get()=="on":
			self.var_entry.set("Online_status: online!")
			acc.set_basic_status(is_online=True)
		elif self.var.get()=="off":
			self.var_entry.set("Online_status: offline")
			acc.set_basic_status(is_online=False)
	
	def create_widgts(self):
		entry=Entry(self.master, textvariable=self.var_entry).pack(side=TOP,expand="yes",fill=X)
		radio_button1=Radiobutton(self.master,text="Online",variable=self.var,value="on",command=self.sel).pack(anchor=W)
		radio_button2=Radiobutton(self.master,text="Offline",variable=self.var,value="off",command=self.sel).pack(anchor=W)						
					
#define function for sending messages when clicking on the button
def sendMessage():
	global buddy_index_now
	msgcontent="Me : "+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())+"\n"
	text_msglist.insert(END,msgcontent,"green")
	msg_get=text_msg.get('0.0',END)
	buddy_list[int(buddy_index_now)].send_pager(str(msg_get))
	text_msglist.insert(END,msg_get)
	text_msg.delete('0.0',END)
	text_msglist.see(END)

#function for quiting the programm	
def app_quit():
	# Shutdown the library
	global acc,lib,transport,root
	acc.delete()
	acc = None
	if pending_pres:
		acc.pres_notify(pending_pres, pj.SubscriptionState.TERMINATED,"rejected")
	transport = None
	lib.destroy()
	lib = None
	exit()
	
#sending typing notificaitons to the buddy
def typing_notify(event):
	global buddy
	if buddy==None:
		pass
	else:
		buddy.send_typing_ind()
#adding buddy 
def add_buddy():
	var_title=StringVar()
	global acc,buddy,var_title,var_contact,buddy_index
	new_buddy=contact_input.get()
	buddy = acc.add_buddy(new_buddy, cb=MyBuddyCallback())
	buddy.subscribe()
	buddy_list.append(buddy)
	contact_list.insert(END, str(buddy_index)+": "+new_buddy)
	var_title="talking with "+new_buddy
	var_contact.set("")
	root.title(var_title)
	buddy_index=buddy_index+1
	
def buddy_select(event):
	global buddy_index_now,var_title
	buddy_index_now=contact_list.get(contact_list.curselection())[0]
	var_title="talking with "+contact_list.get(contact_list.curselection())[2:]
	root.title(var_title)
	

lib = pj.Lib()
# logging config.
lib.init(log_cfg = pj.LogConfig(level=4, callback=log_cb))
#create UDP transport which listens to port 5080
#Transport configuration firstly to appoint IP address with which it will bind.
cfg=pj.TransportConfig()
cfg.port=5060
transport = lib.create_transport(pj.TransportType.UDP,cfg)
#show on which IP address it is listening
print "\nListening on",transport.info().host,":",transport.info().port,"\n"

#start the library
lib.start()

#create a register interface if server is not known
#root_register=Tk()
#root_register.title="Registration"
#root_register.geometry("250x450+510+200")

#add widgts into register interface
#var_server=StringVar()
#label_server=Label(root_register, text="Server-Uri")
#entry=Entry(root_register, textvariable=var_server)
#button_reg=Button(root_register,text="Register", command=register)
#label_server.pack(anchor="s",pady=30)
#entry.pack(expand=YES)
#button_reg.pack(expand=YES,pady=10)

#root_register.mainloop()
#Account configure to create a normal account which can register to the server when the server is known
acc_cfg=pj.AccountConfig("sip:129.187.223.127")
acc_cfg.id="sip:129.187.223.127"
acc_cfg.reg_uri="sip:129.187.223.127"
acc_cfg.proxy=["sip:129.187.223.127;lr"]
acc_cb = MyAccountCallback()
acc=lib.create_account(acc_cfg,cb=acc_cb)
acc_cb.wait()

#create a buddy list
buddy_list=[]
buddy=None
#buddy_index=IntVar()
buddy_index=0
#buddy_index_now=IntVar()
buddy_index_now=0

#create a local account
acc=lib.create_account_for_transport(transport,cb=MyAccountCallback())

#basic layout-setting: Title, Geometry
root=Tk()
root.title("talking with ***")
root.geometry('520x450+300+200')
title_str=StringVar()
				
#add frames
frame_left_top=Frame(root, width=370,height=300)
frame_left_center=Frame(root, width=370,height=120)
frame_left_bottom=Frame(root,width=370,height=25)
frame_right=Frame(root,width=150,height=450)


#set layout of frames
frame_left_top.propagate(0)
frame_left_top.grid(row=0, column=0)
frame_left_center.propagate(0)
frame_left_center.grid(row=1,column=0)
frame_left_bottom.propagate(0)
frame_left_bottom.grid(row=2,column=0)
frame_right.propagate(0)
frame_right.grid(row=0,rowspan=3,column=1)


#add widgts for frames leftside
text_msglist=Text(frame_left_top)
text_msg=Text(frame_left_center)
text_msg.bind('<FocusIn>',typing_notify)
text_msglist.focus_set()
button_sendmsg = Button(frame_left_bottom, text="Send!", command=sendMessage)
sb=Scrollbar(root)
sb.grid(row=0,column=1,sticky=W)
sb.config(command=text_msglist.yview)
text_msglist.tag_config('green',foreground='#008B00')

#widgts for frame_right!
var_listbox=[]
radio_button=RB(frame_right).create_widgts()
contact_list=Listbox(frame_right,listvariable=var_listbox)
contact_list.bind('<ButtonRelease-1>',buddy_select)
var_contact=StringVar()
contact_input=Entry(frame_right,textvariable=var_contact)
addbuddy_button=Button(frame_right, text="add buddy",command=add_buddy)
quit_button = Button(frame_right, text="Quit",command=app_quit)

#insert widgts into frames
text_msglist.pack(expand=YES,fill=X)
text_msg.pack(fill=X)
button_sendmsg.pack(anchor="se",fill=Y)

contact_list.pack(side=TOP,expand=YES,fill=BOTH)
contact_input.pack(fill=Y)
addbuddy_button.pack(anchor="w")
quit_button.pack(anchor="w")

root.mainloop()