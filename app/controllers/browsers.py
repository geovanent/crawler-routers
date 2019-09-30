from app import app
from pathlib import Path
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Chrome(webdriver.Chrome):
    def __init__(self, *args, **kwargs):        
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless') # Hide browser
        options.add_experimental_option(
            "prefs", {
                'download.default_directory' : str(Path().absolute()),
            }
        )

        version_crhome = app.config.get('CRHOME_VERSION')
        if(version_crhome == 77):
            path = r"./chromedriver77.exe"
        else:
            path = r"./chromedriver78.exe"


        super().__init__(executable_path=path,options=options)
    
    def wait_until(self, method, timeout=10, interval=1):
        return WebDriverWait(self, timeout, interval).until(method)
    
    def element(self, locator):
        return self.find_element(*locator)

    @contextmanager
    def frame(self, name):
        self.switch_to.frame(name)
        yield
        self.switch_to.default_content()

    @contextmanager
    def tab(self):
        current = self.current_window_handle
        # open new tab
        self.execute_script('window.open("about:blank", "_blank");')
        # switch to new tab
        self.switch_to_window(self.window_handles[-1])
        
        yield
        
        # close tab
        self.close()
        # switch back to previous tab
        self.switch_to_window(current)

    def wait_downloads(self):
        self.get("chrome://downloads/")
        
        cmd = """
            var items = downloads.Manager.get().items_;
            if (items.every(e => e.state === "COMPLETE"))
                return items.map(e => e.file_path);     
        """

        # waits for all the files to be completed and returns the paths
        return self.wait_until(lambda d: d.execute_script(cmd), timeout=120)

        
def ID(value):
    return By.ID, value

def name(value):
    return By.NAME, value

def css(value):
    return By.CSS_SELECTOR, value

def xpath(value):
    return By.XPATH, value

def link_contains(value):
    return By.PARTIAL_LINK_TEXT, value
    

present = EC.presence_of_element_located
invisible = EC.invisibility_of_element_located


def js_href(el):
    return el.get_attribute('href').partition(':')[-1]
