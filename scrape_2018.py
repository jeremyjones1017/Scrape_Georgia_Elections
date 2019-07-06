from selenium import webdriver
import selenium.webdriver.support.ui as ui
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.firefox.options import Options
import os
import easygui as eg

def main():
	x = 15	#Number of seconds for the wait timers
	#url for the election results
	url = "https://results.enr.clarityelections.com/GA/91639/Web02-state.221451/#/access-to-races"
	
	#Directory for to download the data
	home_dir = eg.diropenbox('','Choose download destination directory')
	
	#List of all the counties in the state
	all_counties = ['Appling','Atkinson','Bacon','Baker','Baldwin','Banks','Barrow','Bartow','Ben_Hill','Berrien',
				'Bibb','Bleckley','Brantley','Brooks','Bryan','Bulloch','Burke','Butts','Calhoun','Camden',
				'Candler','Carroll','Catoosa','Charlton','Chatham','Chattahoochee','Chattooga','Cherokee',
				'Clarke','Clay','Clayton','Clinch','Cobb','Coffee','Colquitt','Columbia','Cook','Coweta',
				'Crawford','Crisp','Dade','Dawson','Decatur','DeKalb','Dodge','Dooly','Dougherty','Douglas',
				'Early','Echols','Effingham','Elbert','Emanuel','Evans','Fannin','Fayette','Floyd','Forsyth',
				'Franklin','Fulton','Gilmer','Glascock','Glynn','Gordon','Grady','Greene','Gwinnett',
				'Habersham','Hall','Hancock','Haralson','Harris','Hart','Heard','Henry','Houston','Irwin',
				'Jackson','Jasper','Jeff_Davis','Jefferson','Jenkins','Johnson','Jones','Lamar','Lanier',
				'Laurens','Lee','Liberty','Lincoln','Long','Lowndes','Lumpkin','Macon','Madison','Marion',
				'McDuffie','McIntosh','Meriwether','Miller','Mitchell','Monroe','Montgomery','Morgan','Murray',
				'Muscogee','Newton','Oconee','Oglethorpe','Paulding','Peach','Pickens','Pierce','Pike','Polk',
				'Pulaski','Putnam','Quitman','Rabun','Randolph','Richmond','Rockdale','Schley','Screven',
				'Seminole','Spalding','Stephens','Stewart','Sumter','Talbot','Taliaferro','Tattnall','Taylor',
				'Telfair','Terrell','Thomas','Tift','Toombs','Towns','Treutlen','Troup','Turner','Twiggs',
				'Union','Upson','Walker','Walton','Ware','Warren','Washington','Wayne','Webster','Wheeler',
				'White','Whitfield','Wilcox','Wilkes','Wilkinson','Worth']

	#Make sure each county has its own directory
	check_directories(all_counties,home_dir)
	#See if any of the data have already been downloaded
	#(useful if some counties fail and you want to retry later)
	counties = check_for_downloads(all_counties,home_dir)
	if counties == all_counties:	#No data has been scraped already
		print('Scraping data for all counties')
	elif len(counties) != 0:		#Some counties have been done, but not all
		print('Scraping data for the following counties: ')
		print(counties)
	else:							#All data have already been downloaded
		print('The data for all counties have already been scraped')
	
	while len(counties) > 0:
		driver = webdriver.Firefox()	#We're using firefox as our browser
		driver.implicitly_wait(x)		#This should let the page load before doing anything
		driver.get(url)					#Open the page with the results
		
		wait(x)		#The implicit wait isn't enough. This makes sure the page loads before we do anything
		
		for county in counties:
			scrape_county(driver,county,x,home_dir)	#Download data for each county
		handles = driver.window_handles		#What tabs are open?
		driver.switch_to.window(handles[0])	#Switch to what should be the only tab left
		driver.close()						#Close the window because (hopefully) we're done
		
		counties = check_for_downloads(all_counties,home_dir)	#Let's see if we're done or not
		done = False
		#If none or only some of the data were downloaded, the user is prompted to try what wasn't done
		#If all of the data were downloaded, we're done!
		if counties == all_counties:
			done_check = input('Something went wrong. Would you like to try again? (Y/N)')
			if done_check == 'n' or done_check == 'N':
				done = True
		elif len(counties) != 0:
			done_check = input("We didn't get it all the first time. Would you like to try again for the following counties? (Y/N) \n{}".format(counties))
			if done_check == 'n' or done_check == 'N':
				done = True
		else:
			print('The data for all counties are all scraped!')
			done = True
			
		if done:
			break
	
def scrape_county(driver,county,x,home_dir):
	'''Does the actual scraping
	Inputs:
		driver - the object that represents the web browser + the web page(s) that are open
		county - the current county we want to scrape data for
		x - the wait time (in seconds)
		home_dir - the target directory for the data
	Outputs:
		None
	'''
	handles = driver.window_handles					#Define the open tabs in the browser
	driver.switch_to.window(handles[0])				#Make sure we're on the main page
	print('Opening {} County Page'.format(county))
	waiting = True
	start_time = time.time()
	while waiting:					#This loop lets us account for errors/delays in the page opening
		try:
			county_link = driver.find_element_by_link_text(county)	#Find the link for our county
			county_link.click()		#Click the link
			waiting = False
		except:
			print('Waiting so we can open the county page')
			end_time = time.time()
			if end_time - start_time > x:	#Check and see if too much time has passed and exit if so
				print('Exiting loop')
				waiting = False
	
	wait(x)	#Wait for the county page to load
	handles = driver.window_handles
	driver.switch_to.window(handles[-1])	#Switch to tab for county
	click_download_links(driver,county,home_dir)		#Download data

def wait(x):
	'''Executes a verbose waiting command. 
	Used instead of a simple "time.sleep(x)" command because I like a bit of a countdown.
	Inputs:
		x - the wait time (in seconds)
	Outputs:
		None
	'''
	print('Waiting {} seconds'.format(x))
	it = 5		#The interval of seconds for the countdown
	while x > 0:
		time.sleep(1)
		x-=1
		if x%it == 0 and x!= 0:
			print('{} seconds remaining'.format(x))

def click_download_links(driver,county,home_dir):
	'''Finds the url for the data and downloads it with curl
	Inputs:
		driver - the object that represents the web browser + the web page(s) that are open
		county - the current county we want to scrape data for
		home_dir - the target directory for the data
	Outputs:
		None
	'''
	county_dir = os.path.join(home_dir,county)
	os.chdir(county_dir)	#Make sure we're in the county directory
	downloads = driver.find_elements_by_class_name('list-download-link')	#Find all download links on the page
	for i,download in enumerate(downloads):
		download_url = download.get_attribute("href")	#Gets url for each download link
		if 'detailtxt.zip' in download_url:		#If it's the one that we want...
			curl_command = 'curl -o detailtxt.zip {}'.format(download_url)	#We download it using curl
			print(curl_command)	#Note the command we're using
			os.system(curl_command)	#Execute the command
	os.chdir(home_dir)	#Change back to the home directory (in the os)
	driver.close()	#close the county results tab

def check_directories(counties,home_dir):
	'''Checks to see if each county directory exists and makes it if it doesn't
	Inputs:
		counties - a list of all the counties
		home_dir - the directory into which all the county directories will go
	Outputs:
		None
	'''
	for county in counties:
		county_dir = os.path.join(home_dir,county)	#The county directory we're looking for
		if not os.path.exists(county_dir):			#If it doesn't exist...
			os.mkdir(county_dir)						#Make it

def check_for_downloads(all_counties,home_dir):
	'''Have we already downloaded the data?
	Inputs:
		all_counties - a list of all the counties
		home_dir - the directory into which all the county directories will go
	Outputs:
		counties - a list of the counties for which data have not been downloaded
	'''
	counties = []
	for county in all_counties:
		county_dir = os.path.join(home_dir,county)				#The directory for the county
		county_file = os.path.join(county_dir,'detailtxt.zip')	#The full path length of the file we're checking on
		if not os.path.exists(county_file):	#If it doesn't exist...
			counties.append(county)				#add the county to the list
	return counties
	
if __name__ == '__main__':
	main()
