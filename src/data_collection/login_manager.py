from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
import shutil, time, os

# Global variable to store the Spotify authorization code
code = ""

def login(profile_src, config):
    """
    Use a previously saved Firefox profile for login.
    
    Args:
        profile_src (str): Path to the source Firefox profile directory
        config (dict): Configuration dictionary with required keys:
            - league_url (str): URL of the music league
            - executable_path (str): Path to geckodriver executable
            
    Returns:
        WebDriver: Selenium WebDriver instance after login or None if failed
    """
    driver = None
    profile_temp = "/tmp/ffx_crawler"
    
    try:
        if profile_src:
            # Clean up existing temp profile
            if os.path.exists(profile_temp):
                try:
                    shutil.rmtree(profile_temp)
                except PermissionError:
                    os.rename(profile_temp, f"{profile_temp}_old_{int(time.time())}")
                    
            # Copy profile with ignore patterns
            ignore_files = shutil.ignore_patterns(
                "lock", ".parentlock", "parent.lock", 
                "sessionstore.jsonlz4", "compatibility.ini"
            )
            shutil.copytree(profile_src, profile_temp, ignore=ignore_files)
            
            # Create Firefox driver with profile
            options = Options()
            options.add_argument("-profile")
            options.add_argument(profile_temp)
            options.add_argument("-headless")
            driver = webdriver.Firefox(options=options, service=Service(executable_path=config.get("executable_path")))
            
            # Navigate to league and refresh
            driver.get(config.get("league_url"))
            time.sleep(3)
            driver.refresh()
            
            # Check if login was successful
            if "invite" in driver.current_url or "login" in driver.current_url:
                raise RuntimeError(f"Previous login failed")
                
        print("Successfully used previous login")
        
    except Exception as e:
        print(f"An error occurred during login: {e}")
        return None
        
    return driver