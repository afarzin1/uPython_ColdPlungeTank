import network
import urequests
import uos
import json
import machine
from time import sleep
import gc
import micropython
import picodebug

class OTAUpdater:
    """ This class handles OTA updates. It connects to the Wi-Fi, checks for updates, downloads and installs them."""
    def __init__(self, deviceName, repo_url, filename):
        self.deviceName = deviceName
        self.filename = filename
        self.repo_url = repo_url

        #self.version_url = self.getLatestVersion()
        #self.version_url = self.process_version_url(repo_url, filename)            # Process the new version url
        fileURL = "https://raw.githubusercontent.com/" + repo_url + "/main/" + filename
        self.firmware_url = fileURL.replace("github.com/repos/","")                            # Removal of the 'main' branch to allow different sources

        # get the current version (stored in version.json)
        if 'version.json' in uos.listdir():    
            with open('version.json') as f:
                self.current_version = json.load(f)['version']
            picodebug.logPrint(f"Current device firmware version is '{self.current_version}'")
            #print(f"Current device firmware version is '{self.current_version}'")

        else:
            self.current_version = "0"
            # save the current version
            with open('version.json', 'w') as f:
                json.dump({'version': self.current_version}, f)
            
    def process_version_url(self, repo_url, filename):
        """ Convert the file's url to its assoicatied version based on Github's oid management."""

        # Necessary URL manipulations
        version_url = repo_url.replace("raw.githubusercontent.com", "github.com")  # Change the domain
        version_url = version_url.replace("/", "§", 4)                             # Temporary change for upcoming replace
        version_url = version_url.replace("/", "/latest-commit/", 1)                # Replacing for latest commit
        version_url = version_url.replace("§", "/", 4)                             # Rollback Temporary change
        version_url = version_url + filename                                       # Add the targeted filename
        
        return version_url
        
    def fetch_latest_code(self)->bool:     
        # Fetch the latest code from the repo.
        #print(self.firmware_url)
        response = urequests.get(self.firmware_url, stream=True)
        if response.status_code == 200:
            picodebug.logPrint(f'Fetching latest firmware code, status: {response.status_code}')
            #print(f'Fetching latest firmware code, status: {response.status_code}')
            chunk_size = 512
            try:
                with open('latest_code.py', 'wb') as f:
                    while True:
                        chunk = response.raw.read(chunk_size)
                        
                        if chunk:
                            f.write(chunk)
                            sleep(0.5)
                        else:
                            break
                picodebug.logPrint(f"Download complete")
                #print(f"Download complete")
                f.close()
                sleep(5)
                return True
            except OSError as e:
                picodebug.logPrint("Connection lost while downloading")
                #print("Connection lost while downloading")
                return False
        else:
            print("Failed to download file")
            return False            

    def update_no_reset(self):
        """ Update the code without resetting the device."""
        
        # update the version in memory
        self.current_version = self.latest_version

        # save the current version
        with open('version.json', 'w') as f:
            json.dump({'version': self.current_version}, f)

        # Overwrite the old code.
        uos.rename('latest_code.py', self.filename)

    def update_and_reset(self):
        """ Update the code and reset the device."""

        picodebug.logPrint('Updating device...')
        #print('Updating device...', end='')

        # Overwrite the old code.
        #uos.rename('latest_code.py', self.filename)  

        # Restart the device to run the new code.
        picodebug.logPrint('Restarting')
        #print("Restarting device... (don't worry about an error message after this")
        sleep(0.25)
        #machine.reset()  # Reset the device to run the new code.
        machine.soft_reset()
        
    def getLatestVersion(self): 
        url_commit = f"https://api.{self.repo_url}/git/ref/heads/main"
        headers = {'User-Agent': self.deviceName}
        response = urequests.get(url_commit,headers=headers)
            
        data = json.loads(response.text)
        
        commit_sha = data["object"]["sha"]
        
        url_tree = f"https://api.{self.repo_url}/git/trees/{commit_sha}"
        response_tree = urequests.get(url_tree,headers=headers)
        tree = json.loads(response_tree.text)

        # Find the blob SHA of the file
        blob_sha = None
        
        for item in tree["tree"]:
            if item["path"] == self.filename:
                blob_sha = item["sha"]
                break

        #if blob_sha:
        #    print(f"The SHA-1 hash of the file is: {blob_sha}")
        #else:
        #    print("File not found in the latest commit of the specified branch.")
        
        latestVersion = blob_sha

        response = ""
        data = ""
        response_tree = ""
        tree = ""
        
        return latestVersion
    
    def check_for_updates(self):
        """ Check if updates are available."""
        
        picodebug.logPrint("Checking for latest version...")
       
        self.latest_version = self.getLatestVersion()
        picodebug.logPrint(f'latest version is: {self.latest_version}')
        #print(f'latest version is: {self.latest_version}')
        
        # compare versions
        newer_version_available = True if self.current_version != self.latest_version else False
        
        picodebug.logPrint(f'Newer version available: {newer_version_available}')
        #print(f'Newer version available: {newer_version_available}')
            
        return newer_version_available
    
    def download_and_install_update_if_available(self):
        """ Check for updates, download and install them."""
        
        if self.check_for_updates():
            if self.fetch_latest_code():
                self.update_no_reset()
                gc.collect()
                self.update_and_reset()
        else:
            picodebug.logPrint("No new updates available")
