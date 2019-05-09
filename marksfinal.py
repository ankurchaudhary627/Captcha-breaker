from selenium import webdriver
from selenium.common.exceptions import NoAlertPresentException
from bs4 import BeautifulSoup
import functools as ft
import re
import csv


import urllib.request
from PIL import Image
import numpy as np
import cv2
from keras.models import load_model
from io import BytesIO

model = load_model('nn_captcha.h5')

def give_captcha(fname):
    left=60
    upper=11
    lower=22
    img=Image.open(fname).convert('L')
    X=[]
    for i in range(1,6):
        right=left+8
        croppedimg=img.crop((left,upper,right,lower))
        np_im = np.array(croppedimg)
        resized_img=cv2.resize(np_im,(28,28), interpolation = cv2.INTER_CUBIC)
        X.append(resized_img.tolist())
        left=right+1
    X=np.array(X)
    num_pixels = X.shape[1] * X.shape[2]
    X = X.reshape(X.shape[0], num_pixels).astype('float32')
    res=model.predict_classes(X)
    captcha=''.join(str(e) for e in res)
    return captcha



#converts marks to grade point
def grade(n):
	if n==100:
		return n//10
	if n>=45:
		return n//10+1
	elif n>=40 and n<45:
		return n//10
	else:
		return 0

#list to store USN, name and calculated sgpa of all students
sgpa=[]

#regular expression to find Student name:
nm='<tdstyle="padding-left:15px"><b>:</b>(\w+[.]?\w+)</td>'
regex=re.compile(nm)

#last valid USN
last=198

url='http://results.vtu.ac.in/resultsvitavicbcs_19/index.php'

driver=webdriver.Chrome(executable_path=r'C:\Users\ankur\Desktop\captcha\chromedriver.exe')   # Create a new instance of the Chrome driver 

# session_url = driver.command_executor._url  
# session_id = driver.session_id
# driver.get(url)

# driver.implicitly_wait(10)


for i in range(1,last+1):
	
	# driver = webdriver.Remote(command_executor=session_url,desired_capabilities={})
	# driver.session_id = session_id
	# driver.get(url)

	#generating the usn
	usn='1cr15cs'
	if i<10:
		usn=usn+'00'+str(i)
	elif i>=10 and i<100:
		usn=usn+'0'+str(i)
	else:
		usn+=str(i)

	driver.get(url)	#fetches the page
	driver.save_screenshot('my_page.png')

	img = driver.find_element_by_xpath('/html/body/div[2]/div/div[2]/div/div/form/div/div[2]/div/div[3]/img')
	location = img.location
	size = img.size
	png = driver.get_screenshot_as_png()
	im = Image.open(BytesIO(png))

	left = location['x']
	top = location['y']
	right = location['x'] + size['width']
	bottom = location['y'] + size['height']
	im = im.crop((left, top, right, bottom)) # defines crop points
	fname='mah_screenshot.png'
	im.save(fname)

	captcha=give_captcha(fname)
	print(captcha)
	ele=driver.find_element_by_name('lns')
	ele.send_keys(usn)
	ele=driver.find_element_by_name('captchacode')
	ele.send_keys(captcha)
	
	try:
		#try checks if the usn is valid or not
		driver.find_element_by_id("submit").click()				
		doc=driver.page_source									#gets the page source the web-site

		doc1=ft.reduce(lambda x,y:x+y,doc.split())				#getting the page source as a string without spaces
		
		x=re.search(regex,doc1)
		if x:
			name=x.group(1)
		
		# driver.quit()

		if re.search(r'Semester:7',doc1):						#checks if the semester is 5
			soup=BeautifulSoup(doc,'lxml')						#creating the BeautifulSoup object
			b=soup.find('div',class_='divTableBody')
			bc1=b.find('div',class_='divTableRow')
			bc3=bc1.findNextSiblings()
			l=[]
			for i in range(8):
				bc4=bc3[i].findChildren()
				x=bc4[4].text
				l.append(x.rstrip(' '))
			
			l=list(map(int,l))									# l contains all subjects marks of a student
			print(l)
			gpa=0.0

			for i in range(0,len(l)):
				if i<3:
					gpa+=(grade(l[i])*4.0)
				elif i<5:
					gpa+=(grade(l[i])*3.0)
				else:
					gpa+=(grade(l[i])*2.0)

			sgpa.append((usn,name.strip(),str(gpa/24.0)))

	except NoAlertPresentException as e:
		continue
	except Exception as e:
		print(e)
		alert = driver.switch_to.alert
		alert.accept()

	
driver.quit()

#sort the list in decreasing order
sgpa=sorted(sgpa,key=lambda x:x[2],reverse=True)
print(sgpa)

#writing the list to a csv file
f=open('cmr-sgpa.csv','w',newline='')
writer=csv.writer(f)
writer.writerow(['USN','Name','SGPA'])
for i in range(len(sgpa)):
	writer.writerow([sgpa[i][0],sgpa[i][1],sgpa[i][2]])
f.close()